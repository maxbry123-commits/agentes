from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from schemas.run_validation import RunValidationCheck, RunValidationReport

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{13,}"),
    re.compile(r"DEEPSEEK_API_KEY\s*=\s*[^\s\"']+"),
]


def validate_run_dir(
    run_dir: Path | str,
    expect_completed: bool = True,
    settings: dict[str, Any] | None = None,
) -> RunValidationReport:
    run_path = Path(run_dir)
    checks: list[RunValidationCheck] = []
    state = _read_state(run_path, checks)
    run_id = str(state.get("run_id") or run_path.name) if isinstance(state, dict) else run_path.name

    if isinstance(state, dict):
        checks.extend(_stage_checks(state, expect_completed))
        checks.extend(_artifact_index_checks(run_path))
        checks.extend(_state_artifact_checks(run_path, state))
        checks.extend(_required_kind_checks(run_path, state, settings or {}))
        checks.extend(_cross_link_checks(run_path, state))
        checks.extend(_secret_scan_checks(run_path))

    blocking = [c.message for c in checks if c.status == "fail" and c.severity == "blocker"]
    warnings = [c.message for c in checks if c.status in {"warn", "fail"} and c.severity != "blocker"]
    score = _score(checks)
    status = "block" if blocking else ("needs_review" if warnings or score < 85 else "pass")

    return RunValidationReport(
        run_id=run_id,
        run_dir=str(run_path),
        status=status,
        score=score,
        checks=checks,
        blocking_issues=blocking,
        warnings=warnings,
        summary=[
            f"status={status}",
            f"score={score}",
            f"checks={len(checks)}",
            f"blocking={len(blocking)}",
            f"warnings={len(warnings)}",
        ],
    )


def report_to_dict(report: RunValidationReport) -> dict[str, Any]:
    return asdict(report)


def _read_state(run_dir: Path, checks: list[RunValidationCheck]) -> dict[str, Any] | None:
    path = run_dir / "state.json"
    if not path.exists():
        checks.append(RunValidationCheck(
            name="state_json",
            status="fail",
            severity="blocker",
            message=f"state.json is missing: {path}",
            evidence={"path": str(path)},
        ))
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        checks.append(RunValidationCheck(
            name="state_json",
            status="fail",
            severity="blocker",
            message=f"state.json cannot be read: {exc}",
            evidence={"path": str(path)},
        ))
        return None
    checks.append(RunValidationCheck(
        name="state_json",
        status="pass",
        severity="info",
        message="state.json exists and is valid JSON",
        evidence={"path": str(path)},
    ))
    return data if isinstance(data, dict) else {}


def _stage_checks(state: dict[str, Any], expect_completed: bool) -> list[RunValidationCheck]:
    stage = str(state.get("stage", ""))
    if not expect_completed:
        return [RunValidationCheck(
            name="state_stage",
            status="pass",
            severity="info",
            message=f"stage={stage}; completed stage not required during workflow",
            evidence={"stage": stage, "expect_completed": expect_completed},
        )]
    return [RunValidationCheck(
        name="state_stage",
        status="pass" if stage == "completed" else "warn",
        severity="warning",
        message="run completed" if stage == "completed" else f"run stage is not completed: {stage}",
        evidence={"stage": stage, "expect_completed": expect_completed},
    )]


def _artifact_index_checks(run_dir: Path) -> list[RunValidationCheck]:
    path = run_dir / "artifact_index.jsonl"
    if not path.exists():
        return [RunValidationCheck(
            name="artifact_index",
            status="warn",
            severity="warning",
            message="artifact_index.jsonl is missing",
            evidence={"path": str(path)},
        )]
    checks: list[RunValidationCheck] = []
    rows = 0
    missing: list[str] = []
    invalid = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            invalid += 1
            continue
        rows += 1
        artifact_path = Path(str(row.get("path", "")))
        if artifact_path and not artifact_path.exists():
            missing.append(str(artifact_path))
    if invalid:
        checks.append(RunValidationCheck(
            name="artifact_index_json",
            status="fail",
            severity="blocker",
            message=f"artifact_index.jsonl contains {invalid} invalid row(s)",
            evidence={"invalid_rows": invalid},
        ))
    if missing:
        checks.append(RunValidationCheck(
            name="artifact_index_paths",
            status="fail",
            severity="blocker",
            message=f"indexed artifact path is missing: {missing[0]}",
            evidence={"missing_count": len(missing), "missing_paths": missing[:10]},
        ))
    if not invalid and not missing:
        checks.append(RunValidationCheck(
            name="artifact_index",
            status="pass",
            severity="info",
            message=f"artifact index is readable with {rows} row(s)",
            evidence={"rows": rows},
        ))
    return checks


def _state_artifact_checks(run_dir: Path, state: dict[str, Any]) -> list[RunValidationCheck]:
    artifacts = state.get("artifacts") or {}
    if not isinstance(artifacts, dict):
        artifacts = {}
    missing: list[str] = []
    for kind, ids in artifacts.items():
        for artifact_id in ids or []:
            folder = run_dir / "artifacts" / str(kind)
            matches = list(folder.glob(f"{artifact_id}.*")) if folder.exists() else []
            if not matches:
                missing.append(f"{kind}/{artifact_id}")
    if missing:
        return [RunValidationCheck(
            name="state_artifacts",
            status="fail",
            severity="blocker",
            message=f"state artifact file is missing: {missing[0]}",
            evidence={"missing_count": len(missing), "missing": missing[:10]},
        )]
    return [RunValidationCheck(
        name="state_artifacts",
        status="pass",
        severity="info",
        message="state-declared artifacts resolve to files",
        evidence={"artifact_kind_count": len(artifacts)},
    )]


def _required_kind_checks(
    run_dir: Path,
    state: dict[str, Any],
    runtime_settings: dict[str, Any],
) -> list[RunValidationCheck]:
    values = state.get("values") or {}
    persisted_settings = values.get("workflow_settings") if isinstance(values.get("workflow_settings"), dict) else {}
    settings = {**persisted_settings, **runtime_settings}
    checks: list[RunValidationCheck] = []
    required = ["reviews", "run_evaluations"]
    if settings.get("enable_experiments") or values.get("experiment_results"):
        required.extend(["experiment_results", "code_patches"])
    if settings.get("enable_retrieval_evaluation") or values.get("retrieval_evaluation"):
        required.append("retrieval_evaluations")
    for kind in required:
        folder = run_dir / "artifacts" / kind
        files = list(folder.glob("*")) if folder.exists() else []
        checks.append(RunValidationCheck(
            name=f"required_{kind}",
            status="pass" if files else "fail",
            severity="blocker" if kind in {"reviews", "run_evaluations", "experiment_results", "code_patches"} else "warning",
            message=f"{kind} artifacts exist" if files else f"required artifact kind is missing: {kind}",
            evidence={"kind": kind, "file_count": len(files)},
        ))
    llm_folder = run_dir / "artifacts" / "llm_calls"
    llm_files = list(llm_folder.glob("*")) if llm_folder.exists() else []
    if settings.get("enable_llm"):
        checks.append(RunValidationCheck(
            name="llm_calls_presence",
            status="pass" if llm_files else "warn",
            severity="info" if llm_files else "warning",
            message="llm_calls artifacts exist" if llm_files else "enable_llm is true but no llm_calls artifacts were found",
            evidence={"enable_llm": True, "file_count": len(llm_files)},
        ))
    else:
        checks.append(RunValidationCheck(
            name="llm_calls_presence",
            status="pass",
            severity="info",
            message="LLM disabled; llm_calls artifacts are optional",
            evidence={"enable_llm": False, "file_count": len(llm_files)},
        ))
    return checks


def _cross_link_checks(run_dir: Path, state: dict[str, Any]) -> list[RunValidationCheck]:
    problems: list[str] = []
    llm_ids = _artifact_ids(run_dir, "llm_calls")
    patch_ids = _json_field_values(run_dir, "code_patches", "patch_id")
    experiment_ids = (
        _json_field_values(run_dir, "experiment_plans", "experiment_id")
        | _json_field_values(run_dir, "branch_experiment_plans", "experiment_id")
        | _state_field_values(state, "experiment_plans", "experiment_id")
    )
    result_experiment_ids = (
        _json_field_values(run_dir, "experiment_results", "experiment_id")
        | _state_field_values(state, "experiment_results", "experiment_id")
    )

    for record in _json_artifacts(run_dir, "auto_debug_records"):
        llm_call_id = str(record.get("llm_call_id", ""))
        if llm_call_id and llm_call_id not in llm_ids:
            problems.append(f"auto_debug_record llm_call_id missing: {llm_call_id}")

    for result in _json_artifacts(run_dir, "experiment_results"):
        patch_id = str(result.get("patch_id", ""))
        if patch_id and patch_id not in patch_ids:
            problems.append(f"experiment_result patch_id missing: {patch_id}")

    for patch in _json_artifacts(run_dir, "code_patches"):
        experiment_id = str(patch.get("experiment_id", ""))
        if experiment_ids and experiment_id and experiment_id not in experiment_ids:
            problems.append(f"code_patch experiment_id has no plan: {experiment_id}")

    for decision in _json_artifacts(run_dir, "experiment_decisions") + _state_records(state, "experiment_decisions"):
        experiment_id = str(decision.get("experiment_id", ""))
        if experiment_id and experiment_id not in result_experiment_ids and experiment_id not in experiment_ids:
            problems.append(f"experiment_decision experiment_id has no result or plan: {experiment_id}")

    return [RunValidationCheck(
        name="artifact_cross_links",
        status="pass" if not problems else "fail",
        severity="blocker",
        message="artifact cross-links are valid" if not problems else problems[0],
        evidence={"problem_count": len(problems), "problems": problems[:10]},
    )]


def _secret_scan_checks(run_dir: Path) -> list[RunValidationCheck]:
    leaks: list[str] = []
    artifacts_dir = run_dir / "artifacts"
    if artifacts_dir.exists():
        for path in artifacts_dir.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".json", ".md", ".txt", ".jsonl"}:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if any(pattern.search(text) for pattern in SECRET_PATTERNS):
                leaks.append(str(path))
    return [RunValidationCheck(
        name="secret_scan",
        status="pass" if not leaks else "fail",
        severity="blocker",
        message="no secret-like values found in artifacts" if not leaks else f"secret-like value found in {leaks[0]}",
        evidence={"leak_count": len(leaks), "paths": leaks[:10]},
    )]


def _artifact_ids(run_dir: Path, kind: str) -> set[str]:
    folder = run_dir / "artifacts" / kind
    if not folder.exists():
        return set()
    return {path.stem for path in folder.iterdir() if path.is_file()}


def _json_artifacts(run_dir: Path, kind: str) -> list[dict[str, Any]]:
    folder = run_dir / "artifacts" / kind
    if not folder.exists():
        return []
    rows: list[dict[str, Any]] = []
    for path in folder.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(data, dict):
            rows.append(data)
    return rows


def _json_field_values(run_dir: Path, kind: str, field: str) -> set[str]:
    return {str(row.get(field, "")) for row in _json_artifacts(run_dir, kind) if row.get(field)}


def _state_records(state: dict[str, Any], key: str) -> list[dict[str, Any]]:
    values = state.get("values") or {}
    value = values.get(key)
    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    if isinstance(value, dict):
        return [row for row in value.values() if isinstance(row, dict)]
    return []


def _state_field_values(state: dict[str, Any], key: str, field: str) -> set[str]:
    return {str(row.get(field, "")) for row in _state_records(state, key) if row.get(field)}


def _score(checks: list[RunValidationCheck]) -> int:
    score = 100
    for check in checks:
        if check.status == "fail" and check.severity == "blocker":
            score -= 30
        elif check.status == "fail":
            score -= 15
        elif check.status == "warn":
            score -= 5
    return max(0, min(100, score))
