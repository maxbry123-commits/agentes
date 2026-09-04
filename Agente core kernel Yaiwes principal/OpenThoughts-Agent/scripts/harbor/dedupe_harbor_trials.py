#!/usr/bin/env python3
"""Remove surplus Harbor trial attempts and rebuild job aggregates."""

from __future__ import annotations

import argparse
import json
import math
import shutil
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from harbor.metrics.mean import Mean
from harbor.models.job.result import JobResult, JobStats
from harbor.models.trial.result import TrialResult


@dataclass(frozen=True)
class DedupeSummary:
    """Counts produced by a Harbor trial deduplication pass."""

    tasks: int
    before: int
    after: int
    removed: int


def _result_paths(job_dir: Path) -> list[Path]:
    return sorted(
        path for path in job_dir.rglob("result.json") if path.parent != job_dir
    )


def _started_at(result: TrialResult) -> datetime:
    value = result.started_at
    if value is None:
        return datetime.max.replace(tzinfo=timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _has_numeric_rewards(result: TrialResult) -> bool:
    rewards = result.verifier_result.rewards if result.verifier_result else None
    return bool(rewards) and all(
        isinstance(value, (int, float)) and math.isfinite(value)
        for value in rewards.values()
    )


def _selected_paths(results: list[tuple[Path, TrialResult]], n_rep: int) -> set[Path]:
    valid = sorted(
        (item for item in results if _has_numeric_rewards(item[1])),
        key=lambda item: (_started_at(item[1]), str(item[0])),
    )
    errored = sorted(
        (item for item in results if not _has_numeric_rewards(item[1])),
        key=lambda item: (_started_at(item[1]), str(item[0])),
    )
    selected: set[Path] = set()
    trial_names: set[str] = set()
    for path, result in valid + errored:
        if result.trial_name in trial_names:
            continue
        selected.add(path)
        trial_names.add(result.trial_name)
        if len(selected) == n_rep:
            break
    return selected


def _canonical_attempts(
    parsed: list[tuple[Path, TrialResult]],
) -> list[tuple[Path, TrialResult]]:
    by_trial_name: dict[str, list[tuple[Path, TrialResult]]] = defaultdict(list)
    for item in parsed:
        by_trial_name[item[1].trial_name].append(item)
    canonical = []
    for copies in by_trial_name.values():
        canonical.append(
            min(
                copies,
                key=lambda item: (
                    not _has_numeric_rewards(item[1]),
                    _started_at(item[1]),
                    len(item[0].parts),
                    str(item[0]),
                ),
            )
        )
    return canonical


def _eval_key(result: TrialResult) -> str:
    model = result.agent_info.model_info.name if result.agent_info.model_info else None
    return JobStats.format_agent_evals_key(
        result.agent_info.name, model, result.source or "adhoc"
    )


def _write_aggregates(job_dir: Path, kept: list[TrialResult]) -> None:
    stats = JobStats.from_trial_results(kept, n_total_trials=len(kept))
    rewards_by_eval: dict[str, list[dict[str, float | int] | None]] = defaultdict(list)
    for result in kept:
        rewards = result.verifier_result.rewards if result.verifier_result else None
        rewards_by_eval[_eval_key(result)].append(rewards)
    for key, rewards in rewards_by_eval.items():
        stats.evals[key].metrics = [Mean().compute(rewards)]

    root_result = job_dir / "result.json"
    existing = (
        JobResult.model_validate_json(root_result.read_text())
        if root_result.exists()
        else None
    )
    starts = [result.started_at for result in kept if result.started_at is not None]
    finishes = [result.finished_at for result in kept if result.finished_at is not None]
    now = datetime.now(timezone.utc)
    aggregate = JobResult(
        id=existing.id if existing else uuid4(),
        started_at=min(starts) if starts else now,
        updated_at=max(finishes) if finishes else now,
        finished_at=max(finishes) if finishes else now,
        n_total_trials=len(kept),
        stats=stats,
    )
    root_result.write_text(aggregate.model_dump_json(indent=4))

    normalized_path = job_dir / "harbor_result.json"
    normalized = (
        json.loads(normalized_path.read_text()) if normalized_path.exists() else {}
    )
    primary_rewards: list[float] = []
    solved = 0
    failed = 0
    for result in kept:
        rewards = result.verifier_result.rewards if result.verifier_result else None
        reward = float(next(iter(rewards.values()), 0.0)) if rewards else 0.0
        primary_rewards.append(reward)
        solved += reward > 0
        failed += result.exception_info is not None
    normalized.update(
        {
            "total_trials": len(kept),
            "solved_trials": solved,
            "failed_trials": failed,
            "mean_reward": sum(primary_rewards) / len(primary_rewards)
            if primary_rewards
            else 0.0,
            "accuracy": solved / len(kept) if kept else 0.0,
        }
    )
    normalized_path.write_text(json.dumps(normalized, indent=2, sort_keys=True))


def _removal_actions(
    removed_paths: list[Path], kept_paths: set[Path]
) -> dict[Path, str]:
    actions: dict[Path, str] = {}
    removed_directories: list[Path] = []
    for path in sorted(removed_paths, key=lambda value: (len(value.parts), str(value))):
        directory = path.parent
        if any(
            directory == ancestor or directory.is_relative_to(ancestor)
            for ancestor in removed_directories
        ):
            actions[path] = "covered"
            continue
        if any(
            kept_path != path and kept_path.is_relative_to(directory)
            for kept_path in kept_paths
        ):
            actions[path] = "file"
            continue
        actions[path] = "directory"
        removed_directories.append(directory)
    return actions


def deduplicate_job(job_dir: Path, n_rep: int, *, apply: bool = False) -> DedupeSummary:
    """Select at most ``n_rep`` score-blind attempts per task.

    Numeric-reward attempts are retained before errored attempts, ordered by start
    time and path. Applying the plan removes only surplus trial directories and
    rebuilds the Harbor aggregate files.
    """
    if n_rep <= 0:
        raise ValueError("n_rep must be positive")
    job_dir = job_dir.resolve()
    if not job_dir.is_dir():
        raise ValueError(f"Job directory does not exist: {job_dir}")

    parsed = [
        (path, TrialResult.model_validate_json(path.read_text()))
        for path in _result_paths(job_dir)
    ]
    by_task: dict[str, list[tuple[Path, TrialResult]]] = defaultdict(list)
    for item in _canonical_attempts(parsed):
        by_task[item[1].task_name].append(item)

    kept_paths: set[Path] = set()
    for task_results in by_task.values():
        kept_paths.update(_selected_paths(task_results, n_rep))
    removed = [(path, result) for path, result in parsed if path not in kept_paths]
    kept = [result for path, result in parsed if path in kept_paths]
    removal_actions = _removal_actions([path for path, _ in removed], kept_paths)
    summary = DedupeSummary(
        tasks=len(by_task), before=len(parsed), after=len(kept), removed=len(removed)
    )
    if not apply:
        return summary

    manifest = {
        "n_rep": n_rep,
        "tasks": summary.tasks,
        "before": summary.before,
        "after": summary.after,
        "removed": [
            {
                "trial_name": result.trial_name,
                "task_name": result.task_name,
                "result_path": str(path.relative_to(job_dir)),
                "had_reward": _has_numeric_rewards(result),
                "started_at": result.started_at.isoformat()
                if result.started_at
                else None,
                "removal_action": removal_actions[path],
            }
            for path, result in removed
        ],
    }
    manifest_path = job_dir / "dedupe_manifest.json"
    if not removed and manifest_path.exists():
        return summary
    for path, _ in removed:
        action = removal_actions[path]
        if action == "directory":
            shutil.rmtree(path.parent)
        elif action == "file":
            path.unlink()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    _write_aggregates(job_dir, kept)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-dir", required=True, type=Path)
    parser.add_argument("--n-rep", required=True, type=int)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    summary = deduplicate_job(args.job_dir, args.n_rep, apply=args.apply)
    print(json.dumps(summary.__dict__, sort_keys=True))


if __name__ == "__main__":
    main()
