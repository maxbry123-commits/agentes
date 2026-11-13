#!/usr/bin/env python3
"""Explain every row lost between Harbor scores, trajectories, and SFT export.

The analyzer accepts one or more local Harbor job directories or durable S3
prefixes. Multiple inputs are treated as separate retry runs. It joins
job-level reward buckets, per-trial results, trajectory artifacts, and the
actual OT-Agent exporter path by trial identity, then writes an exhaustive JSON
report. Run S3 analysis inside an Iris task with the usual object-store
credentials so downloads stay in-region.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import tempfile
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Sequence

from scripts.harbor.cleanup_coreweave_datagen_s3 import CleanupTarget, download_prefix
from scripts.harbor.make_and_upload_trace_dataset import (
    _collect_trial_rows,
    _finalize_chunk,
    _import_traces_utils,
    _install_harbor_patches,
)


SCHEMA_VERSION = 1


@dataclass
class TrialAudit:
    """All raw and exported evidence associated with one Harbor trial identity."""

    source: str
    run: str
    trial_name: str
    trial_directories: set[Path] = field(default_factory=set)
    result_paths: set[Path] = field(default_factory=set)
    trajectory_paths: set[Path] = field(default_factory=set)
    aggregate_numeric_references: int = 0
    direct_numeric_result: bool = False
    direct_rewards: list[dict[str, float]] = field(default_factory=list)
    result_errors: list[str] = field(default_factory=list)
    exports: list[dict[str, Any]] = field(default_factory=list)

    @property
    def numeric(self) -> bool:
        return self.aggregate_numeric_references > 0 or self.direct_numeric_result

    @property
    def numeric_sources(self) -> list[str]:
        sources = []
        if self.aggregate_numeric_references:
            sources.append("aggregate")
        if self.direct_numeric_result:
            sources.append("trial")
        return sources

    @property
    def sft_ready_rows(self) -> int:
        return sum(int(export["sft_ready_rows"]) for export in self.exports)


def _read_json(path: Path) -> tuple[Any | None, str | None]:
    try:
        return json.loads(path.read_text()), None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, f"{type(exc).__name__}: {exc}"


def _is_finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _direct_rewards(payload: Any) -> dict[str, float]:
    if not isinstance(payload, dict):
        return {}
    verifier = payload.get("verifier_result")
    if not isinstance(verifier, dict):
        return {}
    rewards = verifier.get("rewards")
    if isinstance(rewards, dict):
        return {
            str(name): float(value)
            for name, value in rewards.items()
            if _is_finite_number(value)
        }
    reward = verifier.get("reward")
    return {"reward": float(reward)} if _is_finite_number(reward) else {}


def _aggregate_numeric_trial_names(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return []
    stats = payload.get("stats")
    evaluations = stats.get("evals") if isinstance(stats, dict) else None
    if not isinstance(evaluations, dict):
        return []

    names: list[str] = []
    for evaluation in evaluations.values():
        reward_stats = (
            evaluation.get("reward_stats") if isinstance(evaluation, dict) else None
        )
        if not isinstance(reward_stats, dict):
            continue
        for value_map in reward_stats.values():
            if not isinstance(value_map, dict):
                continue
            for reward_value, trial_names in value_map.items():
                try:
                    numeric = math.isfinite(float(reward_value))
                except (TypeError, ValueError):
                    numeric = False
                if not numeric or not isinstance(trial_names, list):
                    continue
                names.extend(str(name) for name in trial_names)
    trial_results = payload.get("trial_results")
    if isinstance(trial_results, list):
        for trial_result in trial_results:
            if _direct_rewards(trial_result) and isinstance(trial_result, dict):
                name = trial_result.get("trial_name")
                if name:
                    names.append(str(name))
    return names


def _is_aggregate(payload: Any) -> bool:
    return isinstance(payload, dict) and isinstance(payload.get("stats"), dict)


def _relative_label(root: Path, path: Path) -> str:
    relative = path.relative_to(root)
    return "." if not relative.parts else relative.as_posix()


def _owning_run(root: Path, directory: Path, aggregate_roots: Sequence[Path]) -> Path:
    owners = [
        candidate
        for candidate in aggregate_roots
        if directory == candidate or directory.is_relative_to(candidate)
    ]
    return max(owners, key=lambda candidate: len(candidate.parts), default=root)


def _trial_name(payload: Any, trial_dir: Path) -> str:
    if isinstance(payload, dict) and payload.get("trial_name"):
        return str(payload["trial_name"])
    return trial_dir.name


def _numeric_gap_reason(audit: TrialAudit) -> str | None:
    if not audit.numeric or audit.trajectory_paths:
        return None
    if not audit.trial_directories:
        return "no_trial_directory"
    if not any((directory / "agent").exists() for directory in audit.trial_directories):
        return "agent_directory_missing"
    return "trajectory_missing"


def _trajectory_preflight_reason(trajectory_path: Path) -> str | None:
    payload, error = _read_json(trajectory_path)
    if error:
        return "invalid_trajectory_json"
    if not isinstance(payload, dict):
        return "trajectory_not_an_object"
    steps = payload.get("steps")
    if not isinstance(steps, list):
        return "steps_missing_or_not_a_list"
    if not any(
        isinstance(step, dict)
        and step.get("source") == "agent"
        and not step.get("is_copied_context")
        for step in steps
    ):
        return "no_agent_steps"
    return None


def _export_trajectory(
    traces_utils: Any,
    trajectory_path: Path,
    *,
    episodes: str,
    success_filter: str | None,
    include_literal_tokens: bool,
) -> dict[str, Any]:
    trial_dir = trajectory_path.parent.parent
    preflight_reason = _trajectory_preflight_reason(trajectory_path)
    if preflight_reason:
        return {
            "trajectory_path": str(trajectory_path),
            "sft_ready_rows": 0,
            "reason": preflight_reason,
        }

    result_path = trial_dir / "result.json"
    if not result_path.is_file():
        return {
            "trajectory_path": str(trajectory_path),
            "sft_ready_rows": 0,
            "reason": "trial_result_missing",
        }
    _, result_error = _read_json(result_path)
    if result_error:
        return {
            "trajectory_path": str(trajectory_path),
            "sft_ready_rows": 0,
            "reason": "trial_result_invalid_json",
            "error": result_error,
        }
    try:
        traces_utils.load_run_metadata(trial_dir)
    except (FileNotFoundError, ValueError) as exc:
        return {
            "trajectory_path": str(trajectory_path),
            "sft_ready_rows": 0,
            "reason": "trial_metadata_invalid",
            "error": f"{type(exc).__name__}: {exc}",
        }

    try:
        rows = _collect_trial_rows(
            traces_utils,
            trial_dir,
            episodes=episodes,
            success_filter=success_filter,
            include_instruction=True,
            include_verifier_output=True,
            verbose=False,
            include_literal_tokens=include_literal_tokens,
        )
    except NotImplementedError as exc:
        return {
            "trajectory_path": str(trajectory_path),
            "sft_ready_rows": 0,
            "reason": "agent_does_not_support_atif",
            "error": str(exc),
        }
    except Exception as exc:
        reason = (
            "multimodal_trajectory"
            if type(exc).__name__ == "MultimodalExportError"
            else "conversation_collection_error"
        )
        return {
            "trajectory_path": str(trajectory_path),
            "sft_ready_rows": 0,
            "reason": reason,
            "error": f"{type(exc).__name__}: {exc}",
        }

    if not rows:
        if success_filter is not None:
            reason = "excluded_by_reward_filter"
        else:
            reason = "exporter_returned_no_rows"
        return {
            "trajectory_path": str(trajectory_path),
            "sft_ready_rows": 0,
            "reason": reason,
        }

    try:
        dataset = traces_utils.rows_to_dataset(rows)
        dataset = _finalize_chunk(dataset)
        ready_rows = len(dataset)
        del dataset
    except Exception as exc:
        return {
            "trajectory_path": str(trajectory_path),
            "collected_rows": len(rows),
            "sft_ready_rows": 0,
            "reason": "dataset_conversion_error",
            "error": f"{type(exc).__name__}: {exc}",
        }

    return {
        "trajectory_path": str(trajectory_path),
        "collected_rows": len(rows),
        "sft_ready_rows": ready_rows,
        "reason": None if ready_rows else "dataset_conversion_removed_all_rows",
    }


def _audit_root(
    root: Path,
    source: str,
    *,
    episodes: str,
    success_filter: str | None,
    include_literal_tokens: bool,
    traces_utils: Any,
) -> tuple[list[TrialAudit], dict[str, int]]:
    result_payloads: dict[Path, tuple[Any | None, str | None]] = {
        path: _read_json(path) for path in sorted(root.rglob("result.json"))
    }
    aggregate_roots = [
        path.parent
        for path, (payload, _) in result_payloads.items()
        if _is_aggregate(payload)
    ]
    audits: dict[tuple[Path, str], TrialAudit] = {}

    def audit_for(run_root: Path, name: str) -> TrialAudit:
        key = (run_root, name)
        if key not in audits:
            audits[key] = TrialAudit(
                source=source,
                run=_relative_label(root, run_root),
                trial_name=name,
            )
        return audits[key]

    aggregate_references = 0
    for result_path, (payload, _) in result_payloads.items():
        if not _is_aggregate(payload):
            continue
        for name in _aggregate_numeric_trial_names(payload):
            aggregate_references += 1
            audit_for(result_path.parent, name).aggregate_numeric_references += 1

    aggregate_paths = {run_root / "result.json" for run_root in aggregate_roots}
    for result_path, (payload, error) in result_payloads.items():
        if result_path in aggregate_paths:
            continue
        trial_dir = result_path.parent
        run_root = _owning_run(root, trial_dir, aggregate_roots)
        audit = audit_for(run_root, _trial_name(payload, trial_dir))
        audit.trial_directories.add(trial_dir)
        audit.result_paths.add(result_path)
        if error:
            audit.result_errors.append(error)
            continue
        rewards = _direct_rewards(payload)
        if rewards:
            audit.direct_numeric_result = True
            audit.direct_rewards.append(rewards)

    for trajectory_path in sorted(root.rglob("agent/trajectory.json")):
        trial_dir = trajectory_path.parent.parent
        run_root = _owning_run(root, trial_dir, aggregate_roots)
        matching = [
            audit
            for (candidate_run, _), audit in audits.items()
            if candidate_run == run_root and trial_dir in audit.trial_directories
        ]
        audit = (
            matching[0] if len(matching) == 1 else audit_for(run_root, trial_dir.name)
        )
        audit.trial_directories.add(trial_dir)
        audit.trajectory_paths.add(trajectory_path)
        audit.exports.append(
            _export_trajectory(
                traces_utils,
                trajectory_path,
                episodes=episodes,
                success_filter=success_filter,
                include_literal_tokens=include_literal_tokens,
            )
        )

    counts = {
        "aggregate_numeric_references": aggregate_references,
        "result_files": len(result_payloads) - len(aggregate_paths),
        "aggregate_result_files": len(aggregate_paths),
    }
    return list(audits.values()), counts


def _audit_to_dict(audit: TrialAudit) -> dict[str, Any]:
    numeric_gap_reason = _numeric_gap_reason(audit)
    return {
        "source": audit.source,
        "run": audit.run,
        "trial_name": audit.trial_name,
        "numeric_result": audit.numeric,
        "numeric_sources": audit.numeric_sources,
        "aggregate_numeric_references": audit.aggregate_numeric_references,
        "direct_rewards": audit.direct_rewards,
        "trial_directories": sorted(str(path) for path in audit.trial_directories),
        "result_paths": sorted(str(path) for path in audit.result_paths),
        "result_errors": audit.result_errors,
        "trajectory_paths": sorted(str(path) for path in audit.trajectory_paths),
        "numeric_to_trajectory_reason": numeric_gap_reason,
        "exports": audit.exports,
        "sft_ready_rows": audit.sft_ready_rows,
    }


def analyze_dataset(
    dataset_roots: Sequence[Path],
    *,
    source_names: Sequence[str] | None = None,
    episodes: str = "last",
    success_filter: str | None = None,
    include_literal_tokens: bool = False,
) -> dict[str, Any]:
    """Return a complete per-trial accounting of both SFT export boundaries."""
    if not dataset_roots:
        raise ValueError("At least one dataset root is required")
    if source_names is not None and len(source_names) != len(dataset_roots):
        raise ValueError("source_names must align with dataset_roots")

    traces_utils = _import_traces_utils()
    _install_harbor_patches(include_literal_tokens=include_literal_tokens)
    all_audits: list[TrialAudit] = []
    source_counts: list[dict[str, Any]] = []
    for index, raw_root in enumerate(dataset_roots):
        root = Path(raw_root).resolve()
        if not root.is_dir():
            raise ValueError(f"Dataset root does not exist: {root}")
        source = source_names[index] if source_names is not None else str(root)
        audits, counts = _audit_root(
            root,
            source,
            episodes=episodes,
            success_filter=success_filter,
            include_literal_tokens=include_literal_tokens,
            traces_utils=traces_utils,
        )
        all_audits.extend(audits)
        source_counts.append({"source": source, **counts})

    numeric_gap_reasons = Counter(
        reason
        for audit in all_audits
        if (reason := _numeric_gap_reason(audit)) is not None
    )
    export_gap_reasons = Counter(
        export["reason"]
        for audit in all_audits
        for export in audit.exports
        if export["sft_ready_rows"] == 0
    )
    aggregate_references = sum(
        item["aggregate_numeric_references"] for item in source_counts
    )
    numeric_identities = sum(audit.numeric for audit in all_audits)
    trajectory_files = sum(len(audit.trajectory_paths) for audit in all_audits)
    collected_rows = sum(
        int(export.get("collected_rows", 0))
        for audit in all_audits
        for export in audit.exports
    )
    sft_ready_rows = sum(audit.sft_ready_rows for audit in all_audits)
    summary = {
        "numeric_result_identities": numeric_identities,
        "aggregate_numeric_result_identities": sum(
            audit.aggregate_numeric_references > 0 for audit in all_audits
        ),
        "aggregate_numeric_references": aggregate_references,
        "duplicate_aggregate_numeric_references": sum(
            max(0, audit.aggregate_numeric_references - 1) for audit in all_audits
        ),
        "direct_numeric_result_identities": sum(
            audit.direct_numeric_result for audit in all_audits
        ),
        "numeric_identities_with_trajectory": sum(
            audit.numeric and bool(audit.trajectory_paths) for audit in all_audits
        ),
        "trajectory_trial_identities": sum(
            bool(audit.trajectory_paths) for audit in all_audits
        ),
        "trajectory_files": trajectory_files,
        "trajectory_files_with_sft_rows": sum(
            export["sft_ready_rows"] > 0
            for audit in all_audits
            for export in audit.exports
        ),
        "collected_conversation_rows": collected_rows,
        "sft_ready_rows": sft_ready_rows,
        "trajectory_file_to_sft_row_delta": trajectory_files - sft_ready_rows,
        "numeric_to_trajectory_gap": sum(numeric_gap_reasons.values()),
        "trajectory_to_sft_gap": sum(export_gap_reasons.values()),
        "numeric_to_trajectory_reasons": dict(sorted(numeric_gap_reasons.items())),
        "trajectory_to_sft_reasons": dict(sorted(export_gap_reasons.items())),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "settings": {
            "episodes": episodes,
            "success_filter": success_filter or "none",
            "include_literal_tokens": include_literal_tokens,
        },
        "sources": source_counts,
        "summary": summary,
        "trials": sorted(
            (_audit_to_dict(audit) for audit in all_audits),
            key=lambda record: (record["source"], record["run"], record["trial_name"]),
        ),
    }


@contextmanager
def materialized_datasets(
    inputs: Sequence[str],
) -> Iterator[tuple[list[Path], list[str]]]:
    """Materialize local paths and S3 prefixes into analyzable local roots."""
    temporary_root = Path(tempfile.mkdtemp(prefix="sft-export-gap-"))
    roots: list[Path] = []
    try:
        for index, value in enumerate(inputs):
            if value.startswith("s3://"):
                destination = temporary_root / f"source-{index:02d}"
                target = CleanupTarget(
                    f"analysis-{index:02d}", (value,), "unused/unused"
                )
                download_prefix(target, destination)
                roots.append(destination)
            else:
                roots.append(Path(value))
        yield roots, list(inputs)
    finally:
        shutil.rmtree(temporary_root)


def _print_summary(report: dict[str, Any], output: Path) -> None:
    summary = report["summary"]
    print(f"Numeric result identities: {summary['numeric_result_identities']}")
    print(f"Trajectory files: {summary['trajectory_files']}")
    print(f"SFT-ready rows: {summary['sft_ready_rows']}")
    print(f"Numeric -> trajectory gap: {summary['numeric_to_trajectory_gap']}")
    for reason, count in summary["numeric_to_trajectory_reasons"].items():
        print(f"  {reason}: {count}")
    print(f"Trajectory -> SFT gap: {summary['trajectory_to_sft_gap']}")
    for reason, count in summary["trajectory_to_sft_reasons"].items():
        print(f"  {reason}: {count}")
    print(f"Detailed report: {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        action="append",
        required=True,
        help="Local Harbor job directory or s3:// durable prefix; repeat for retries",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("sft-export-gap-analysis.json")
    )
    parser.add_argument("--episodes", choices=("all", "last"), default="last")
    parser.add_argument(
        "--filter", choices=("none", "success", "failure"), default="none"
    )
    parser.add_argument("--include-literal-tokens", action="store_true")
    args = parser.parse_args()

    with materialized_datasets(args.dataset) as (roots, source_names):
        report = analyze_dataset(
            roots,
            source_names=source_names,
            episodes=args.episodes,
            success_filter=None if args.filter == "none" else args.filter,
            include_literal_tokens=args.include_literal_tokens,
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    _print_summary(report, args.output)


if __name__ == "__main__":
    main()
