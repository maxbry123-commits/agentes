# P17: Run Validation And Delivery Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic run artifact validation, post-run CLI validation, dynamic smoke verification, and current handoff documentation so P8-P16 can be delivered to another developer.

**Architecture:** Add a schema-backed validation layer separate from `RunEvaluationAgent`. `RunValidationAgent` writes `run_validations` artifacts during workflow execution, while `app.main validate-run` validates completed run directories from disk. Dynamic validation uses real CLI runs plus `validate-run --strict`.

**Tech Stack:** Python standard library, `dataclasses`, `unittest`, existing `ArtifactStore`, existing `Workflow`, existing CLI parser, existing docs under `docs/`.

---

## File Map

Create:

- `schemas/run_validation.py`: dataclasses for validation checks and reports.
- `tools/run_artifact_validator.py`: deterministic run directory validator.
- `agents/run_validation_agent.py`: workflow agent wrapper around the validator.
- `tests/test_run_artifact_validator.py`: validator and CLI tests.
- `docs/p17_dynamic_validation.md`: run matrix and expected outcomes.

Modify:

- `core/workflow.py`: persist public workflow settings into `state.values["workflow_settings"]`.
- `agents/__init__.py`: export `RunValidationAgent`.
- `workflows/factory.py`: insert `RunValidationAgent` after `RunEvaluationAgent`.
- `app/main.py`: add `validate-run` CLI command.
- `docs/project_handoff.md`: update current status to P17 and current test count.
- `docs/Q&A.md`: add P17 operational Q&A.

Do not modify:

- `Intent-LED-mul-agent` target repository.
- `.env`.
- Local paper library paths.
- `external/AgentLaboratory`.

---

## Task 1: Add Run Validation Schema

**Files:**
- Create: `schemas/run_validation.py`
- Test: `tests/test_run_artifact_validator.py`

- [ ] **Step 1: Write schema tests**

Create `tests/test_run_artifact_validator.py` with the first tests:

```python
from __future__ import annotations

from dataclasses import asdict
from unittest import TestCase, main

from schemas.run_validation import RunValidationCheck, RunValidationReport


class RunValidationSchemaTest(TestCase):
    def test_check_defaults_are_jsonable(self):
        check = RunValidationCheck(
            name="state_exists",
            status="pass",
            severity="info",
            message="state.json exists",
            evidence={"path": "state.json"},
        )
        payload = asdict(check)
        self.assertEqual(payload["name"], "state_exists")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["severity"], "info")
        self.assertEqual(payload["evidence"]["path"], "state.json")

    def test_report_defaults_are_jsonable(self):
        report = RunValidationReport(
            run_id="run_1",
            run_dir="data/runs/run_1",
            status="pass",
            score=100,
            checks=[],
            blocking_issues=[],
            warnings=[],
            summary=["status=pass"],
        )
        payload = asdict(report)
        self.assertTrue(payload["validation_id"].startswith("runval_"))
        self.assertEqual(payload["run_id"], "run_1")
        self.assertEqual(payload["score"], 100)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run schema tests and verify they fail**

Run:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_run_artifact_validator.RunValidationSchemaTest
```

Expected: FAIL with `ModuleNotFoundError: No module named 'schemas.run_validation'`.

- [ ] **Step 3: Implement schema**

Create `schemas/run_validation.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from schemas.base import new_id


@dataclass(slots=True)
class RunValidationCheck:
    name: str
    status: str
    severity: str
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RunValidationReport:
    run_id: str
    run_dir: str
    status: str
    score: int
    checks: list[RunValidationCheck] = field(default_factory=list)
    blocking_issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    summary: list[str] = field(default_factory=list)
    validation_id: str = field(default_factory=lambda: new_id("runval"))
```

- [ ] **Step 4: Run schema tests and verify they pass**

Run:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_run_artifact_validator.RunValidationSchemaTest
```

Expected: `Ran 2 tests ... OK`.

---

## Task 2: Implement Run Artifact Validator Core

**Files:**
- Create: `tools/run_artifact_validator.py`
- Modify: `tests/test_run_artifact_validator.py`

- [ ] **Step 1: Add validator tests for run directory integrity**

Append to `tests/test_run_artifact_validator.py`:

```python
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.run_artifact_validator import validate_run_dir


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class RunArtifactValidatorTest(TestCase):
    def test_valid_minimal_run_passes(self):
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "runs" / "run_1"
            _write_json(run_dir / "state.json", {
                "run_id": "run_1",
                "stage": "completed",
                "values": {"enable_experiments": False},
                "artifacts": {"reviews": ["review_1"], "run_evaluations": ["eval_1"]},
            })
            _write_json(run_dir / "artifacts" / "reviews" / "review_1.json", {"review_id": "review_1"})
            _write_json(run_dir / "artifacts" / "run_evaluations" / "eval_1.json", {"evaluation_id": "eval_1"})
            (run_dir / "artifact_index.jsonl").write_text(
                json.dumps({"kind": "reviews", "artifact_id": "review_1", "path": str(run_dir / "artifacts" / "reviews" / "review_1.json")}) + "\n",
                encoding="utf-8",
            )

            report = validate_run_dir(run_dir, expect_completed=True)

            self.assertEqual(report.status, "pass")
            self.assertEqual(report.blocking_issues, [])

    def test_missing_state_blocks(self):
        with TemporaryDirectory() as tmp:
            report = validate_run_dir(Path(tmp) / "missing_run", expect_completed=True)
            self.assertEqual(report.status, "block")
            self.assertTrue(any("state.json" in issue for issue in report.blocking_issues))

    def test_missing_indexed_file_blocks(self):
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "runs" / "run_1"
            _write_json(run_dir / "state.json", {
                "run_id": "run_1",
                "stage": "completed",
                "values": {},
                "artifacts": {},
            })
            missing = run_dir / "artifacts" / "reports" / "missing.md"
            (run_dir / "artifact_index.jsonl").parent.mkdir(parents=True, exist_ok=True)
            (run_dir / "artifact_index.jsonl").write_text(
                json.dumps({"kind": "reports", "artifact_id": "missing", "path": str(missing)}) + "\n",
                encoding="utf-8",
            )

            report = validate_run_dir(run_dir, expect_completed=True)

            self.assertEqual(report.status, "block")
            self.assertTrue(any("indexed artifact path is missing" in issue for issue in report.blocking_issues))

    def test_state_artifact_without_file_blocks(self):
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "runs" / "run_1"
            _write_json(run_dir / "state.json", {
                "run_id": "run_1",
                "stage": "completed",
                "values": {},
                "artifacts": {"reviews": ["review_missing"]},
            })

            report = validate_run_dir(run_dir, expect_completed=True)

            self.assertEqual(report.status, "block")
            self.assertTrue(any("state artifact file is missing" in issue for issue in report.blocking_issues))

    def test_llm_disabled_missing_llm_calls_is_info(self):
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "runs" / "run_1"
            _write_json(run_dir / "state.json", {
                "run_id": "run_1",
                "stage": "completed",
                "values": {"workflow_settings": {"enable_llm": False}},
                "artifacts": {
                    "reviews": ["review_1"],
                    "run_evaluations": ["eval_1"],
                },
            })
            _write_json(run_dir / "artifacts" / "reviews" / "review_1.json", {"review_id": "review_1"})
            _write_json(run_dir / "artifacts" / "run_evaluations" / "eval_1.json", {"evaluation_id": "eval_1"})

            report = validate_run_dir(run_dir, expect_completed=True)
            check = next(c for c in report.checks if c.name == "llm_calls_presence")

            self.assertEqual(check.status, "pass")
            self.assertEqual(check.severity, "info")

    def test_llm_enabled_missing_llm_calls_warns(self):
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "runs" / "run_1"
            _write_json(run_dir / "state.json", {
                "run_id": "run_1",
                "stage": "completed",
                "values": {"workflow_settings": {"enable_llm": True}},
                "artifacts": {
                    "reviews": ["review_1"],
                    "run_evaluations": ["eval_1"],
                },
            })
            _write_json(run_dir / "artifacts" / "reviews" / "review_1.json", {"review_id": "review_1"})
            _write_json(run_dir / "artifacts" / "run_evaluations" / "eval_1.json", {"evaluation_id": "eval_1"})

            report = validate_run_dir(run_dir, expect_completed=True)
            check = next(c for c in report.checks if c.name == "llm_calls_presence")

            self.assertEqual(check.status, "warn")
            self.assertEqual(check.severity, "warning")
```

- [ ] **Step 2: Run validator tests and verify they fail**

Run:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_run_artifact_validator.RunArtifactValidatorTest
```

Expected: FAIL with `ModuleNotFoundError: No module named 'tools.run_artifact_validator'`.

- [ ] **Step 3: Implement validator core**

Create `tools/run_artifact_validator.py`:

```python
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
```

- [ ] **Step 4: Run validator tests**

Run:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_run_artifact_validator.RunArtifactValidatorTest
```

Expected: tests pass.

---

## Task 3: Add Cross-Link And Secret-Leak Tests

**Files:**
- Modify: `tests/test_run_artifact_validator.py`
- Modify: `tools/run_artifact_validator.py` only if tests reveal gaps

- [ ] **Step 1: Add cross-link and secret tests**

Append to `RunArtifactValidatorTest`:

```python
    def test_auto_debug_llm_call_link_missing_blocks(self):
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "runs" / "run_1"
            _write_json(run_dir / "state.json", {
                "run_id": "run_1",
                "stage": "completed",
                "values": {},
                "artifacts": {},
            })
            _write_json(run_dir / "artifacts" / "auto_debug_records" / "debug_1.json", {
                "record_id": "debug_1",
                "llm_call_id": "llm_call_missing",
            })

            report = validate_run_dir(run_dir, expect_completed=True)

            self.assertEqual(report.status, "block")
            self.assertTrue(any("llm_call_id" in issue for issue in report.blocking_issues))

    def test_experiment_result_patch_link_missing_blocks(self):
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "runs" / "run_1"
            _write_json(run_dir / "state.json", {
                "run_id": "run_1",
                "stage": "completed",
                "values": {"experiment_results": [{"status": "passed"}]},
                "artifacts": {},
            })
            _write_json(run_dir / "artifacts" / "experiment_results" / "result_1.json", {
                "result_id": "result_1",
                "experiment_id": "exp_1",
                "patch_id": "patch_missing",
                "status": "passed",
            })

            report = validate_run_dir(run_dir, expect_completed=True)

            self.assertEqual(report.status, "block")
            self.assertTrue(any("patch_id" in issue for issue in report.blocking_issues))

    def test_code_patch_experiment_id_uses_state_plan_fallback(self):
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "runs" / "run_1"
            _write_json(run_dir / "state.json", {
                "run_id": "run_1",
                "stage": "completed",
                "values": {"experiment_plans": [{"experiment_id": "exp_state"}]},
                "artifacts": {
                    "reviews": ["review_1"],
                    "run_evaluations": ["eval_1"],
                    "code_patches": ["patch_1"],
                },
            })
            _write_json(run_dir / "artifacts" / "reviews" / "review_1.json", {"review_id": "review_1"})
            _write_json(run_dir / "artifacts" / "run_evaluations" / "eval_1.json", {"evaluation_id": "eval_1"})
            _write_json(run_dir / "artifacts" / "code_patches" / "patch_1.json", {
                "patch_id": "patch_1",
                "experiment_id": "exp_state",
            })

            report = validate_run_dir(run_dir, expect_completed=True)

            self.assertNotIn("code_patch experiment_id has no plan: exp_state", report.blocking_issues)

    def test_experiment_decision_uses_state_plan_fallback(self):
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "runs" / "run_1"
            _write_json(run_dir / "state.json", {
                "run_id": "run_1",
                "stage": "completed",
                "values": {
                    "experiment_plans": [{"experiment_id": "exp_state"}],
                    "experiment_decisions": {"exp_state": {"experiment_id": "exp_state", "decision": "continue"}},
                },
                "artifacts": {
                    "reviews": ["review_1"],
                    "run_evaluations": ["eval_1"],
                },
            })
            _write_json(run_dir / "artifacts" / "reviews" / "review_1.json", {"review_id": "review_1"})
            _write_json(run_dir / "artifacts" / "run_evaluations" / "eval_1.json", {"evaluation_id": "eval_1"})

            report = validate_run_dir(run_dir, expect_completed=True)

            self.assertNotIn("experiment_decision experiment_id has no result or plan: exp_state", report.blocking_issues)

    def test_secret_like_token_blocks(self):
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "runs" / "run_1"
            _write_json(run_dir / "state.json", {
                "run_id": "run_1",
                "stage": "completed",
                "values": {},
                "artifacts": {},
            })
            (run_dir / "artifacts" / "reports").mkdir(parents=True, exist_ok=True)
            (run_dir / "artifacts" / "reports" / "bad.md").write_text(
                "leaked key sk-abcdefghijklmnop",
                encoding="utf-8",
            )

            report = validate_run_dir(run_dir, expect_completed=True)

            self.assertEqual(report.status, "block")
            self.assertTrue(any("secret-like" in issue for issue in report.blocking_issues))
```

- [ ] **Step 2: Run cross-link tests**

Run:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_run_artifact_validator.RunArtifactValidatorTest
```

Expected: tests pass. If a test fails, fix `tools/run_artifact_validator.py` while preserving the behavior specified in the test names.

---

## Task 4: Add RunValidationAgent And Workflow Integration

**Files:**
- Modify: `core/workflow.py`
- Create: `agents/run_validation_agent.py`
- Modify: `agents/__init__.py`
- Modify: `workflows/factory.py`
- Modify: `tests/test_full_research_loop.py`
- Modify: `tests/test_run_artifact_validator.py`

- [ ] **Step 1: Add workflow settings persistence test**

Append to `tests/test_run_artifact_validator.py`:

```python
from core.agent_base import Agent, AgentContext, AgentResult
from core.artifact_store import ArtifactStore
from schemas.topic_pack import TopicPack
from core.workflow import Workflow
from core.run_logger import RunLogger


class NoopAgent(Agent):
    name = "noop_agent"

    def run(self, state, context):
        return AgentResult()


class WorkflowSettingsPersistenceTest(TestCase):
    def test_workflow_persists_public_settings_in_state(self):
        with TemporaryDirectory() as tmp:
            store = ArtifactStore(Path(tmp) / "runs")
            workflow = Workflow(
                name="test_workflow",
                agents=[NoopAgent()],
                artifact_store=store,
                memory_store=None,
                tool_registry=None,
                logger=RunLogger(),
                settings={
                    "enable_experiments": True,
                    "enable_llm": False,
                    "llm_call_budget": 0,
                    "llm_token_budget": 12000,
                    "llm_tokens_used": 0,
                    "deepseek_api_key": "sk-should-not-persist",
                    "session_token": "credential-should-not-persist",
                },
            )

            state = workflow.run(TopicPack(topic_name="test"))

            self.assertEqual(state.values["workflow_settings"]["enable_experiments"], True)
            self.assertEqual(state.values["workflow_settings"]["enable_llm"], False)
            self.assertEqual(state.values["workflow_settings"]["llm_call_budget"], 0)
            self.assertEqual(state.values["workflow_settings"]["llm_token_budget"], 12000)
            self.assertEqual(state.values["workflow_settings"]["llm_tokens_used"], 0)
            self.assertNotIn("deepseek_api_key", state.values["workflow_settings"])
            self.assertNotIn("session_token", state.values["workflow_settings"])
```

- [ ] **Step 2: Run workflow settings test and verify it fails**

Run:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_run_artifact_validator.WorkflowSettingsPersistenceTest
```

Expected: FAIL because `workflow_settings` is not persisted.

- [ ] **Step 3: Persist public workflow settings**

Modify `core/workflow.py`.

Add this helper near the imports:

```python
SENSITIVE_SETTING_NAMES = {
    "api_key",
    "apikey",
    "secret",
    "token",
}


def _is_sensitive_setting_key(key: object) -> bool:
    name = str(key).lower()
    return (
        name in SENSITIVE_SETTING_NAMES
        or name.endswith("_api_key")
        or name.endswith("_secret")
        or name.endswith("_token")
        or name.endswith("_access_token")
        or name.endswith("_refresh_token")
        or name.endswith("_auth_token")
    )


def _public_workflow_settings(settings: dict) -> dict:
    public: dict = {}
    for key, value in settings.items():
        if _is_sensitive_setting_key(key):
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            public[str(key)] = value
        elif isinstance(value, (list, tuple)):
            public[str(key)] = list(value)
        elif isinstance(value, dict):
            public[str(key)] = {
                str(k): v for k, v in value.items()
                if not _is_sensitive_setting_key(k)
                and (isinstance(v, (str, int, float, bool)) or v is None)
            }
    return public
```

Then in `Workflow.run()`, immediately after `state = ResearchState(topic=topic)`:

```python
        state.values["workflow_settings"] = _public_workflow_settings(self.settings)
```

- [ ] **Step 4: Run workflow settings test**

Run:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_run_artifact_validator.WorkflowSettingsPersistenceTest
```

Expected: test passes.

- [ ] **Step 5: Add agent test**

Append to `tests/test_run_artifact_validator.py`:

```python
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState
from schemas.topic_pack import TopicPack
from agents.run_validation_agent import RunValidationAgent


class RunValidationAgentTest(TestCase):
    def test_agent_writes_validation_artifact(self):
        with TemporaryDirectory() as tmp:
            store = ArtifactStore(Path(tmp) / "runs")
            state = ResearchState(topic=TopicPack(topic_name="test"))
            run_dir = store.run_dir(state.run_id)
            state.artifacts["reviews"] = ["review_1"]
            state.artifacts["run_evaluations"] = ["eval_1"]
            store.save_state(state.run_id, state.to_dict())
            store.save_json(state.run_id, "reviews", "review_1", {"review_id": "review_1"})
            store.save_json(state.run_id, "run_evaluations", "eval_1", {"evaluation_id": "eval_1"})
            context = AgentContext(
                artifact_store=store,
                memory_store=None,
                tool_registry=None,
                settings={},
            )

            result = RunValidationAgent().run(state, context)

            self.assertIn("run_validations", result.artifacts)
            self.assertIn("run_validation", state.values)
            self.assertTrue(store.list_artifacts(state.run_id, "run_validations"))
```

- [ ] **Step 6: Run agent test and verify it fails**

Run:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_run_artifact_validator.RunValidationAgentTest
```

Expected: FAIL with `ModuleNotFoundError: No module named 'agents.run_validation_agent'`.

- [ ] **Step 7: Implement agent**

Create `agents/run_validation_agent.py`:

```python
from __future__ import annotations

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from tools.run_artifact_validator import report_to_dict, validate_run_dir


class RunValidationAgent(Agent):
    name = "run_validation_agent"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        run_dir = context.artifact_store.run_dir(state.run_id)
        report = validate_run_dir(
            run_dir,
            expect_completed=False,
            settings=context.settings,
        )
        payload = report_to_dict(report)
        context.artifact_store.save_json(
            state.run_id,
            "run_validations",
            report.validation_id,
            payload,
        )
        state.values["run_validation"] = payload
        state.values["run_validation_status"] = report.status
        state.values["run_validation_score"] = report.score
        return AgentResult(
            notes=[f"run validation status={report.status} score={report.score}"],
            artifacts={"run_validations": [report.validation_id]},
            values={
                "run_validation": payload,
                "run_validation_status": report.status,
                "run_validation_score": report.score,
            },
        )
```

- [ ] **Step 8: Export agent**

Modify `agents/__init__.py`:

```python
from agents.run_validation_agent import RunValidationAgent
```

Add `"RunValidationAgent"` to `__all__`.

- [ ] **Step 9: Integrate workflow**

Modify `workflows/factory.py` imports to include `RunValidationAgent`.

Then change the ending sequence:

```python
    agents.append(ReviewerAgent())
    agents.append(RunEvaluationAgent())
    agents.append(RunValidationAgent())
    agents.append(LiteratureMemoryPersistenceAgent(lit_memory_store=literature_memory_store))
```

- [ ] **Step 10: Add workflow-order test**

Append to `tests/test_full_research_loop.py`:

```python
class RunValidationWorkflowIntegrationTest(TestCase):
    def test_run_validation_agent_runs_after_run_evaluator(self):
        from core.artifact_store import ArtifactStore
        from core.run_logger import RunLogger
        from tools.tool_registry import build_default_tool_registry
        from workflows.factory import build_full_research_workflow

        with TemporaryDirectory() as tmp:
            workflow = build_full_research_workflow(
                artifact_store=ArtifactStore(Path(tmp) / "runs"),
                memory_store=None,
                tool_registry=build_default_tool_registry(),
                logger=RunLogger(),
            )
            names = [agent.name for agent in workflow.agents]
            self.assertIn("run_evaluator", names)
            self.assertIn("run_validation_agent", names)
            self.assertLess(names.index("run_evaluator"), names.index("run_validation_agent"))
```

If `TemporaryDirectory`, `Path`, or `TestCase` are not imported in that file, add imports at the top:

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
```

- [ ] **Step 11: Run integration tests**

Run:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_run_artifact_validator tests.test_full_research_loop
```

Expected: tests pass.

---

## Task 5: Add `validate-run` CLI

**Files:**
- Modify: `app/main.py`
- Modify: `tests/test_run_artifact_validator.py`

- [ ] **Step 1: Add CLI parser test**

Append to `tests/test_run_artifact_validator.py`:

```python
class ValidateRunCliParserTest(TestCase):
    def test_validate_run_parser(self):
        from app.main import build_parser

        parser = build_parser()
        args = parser.parse_args([
            "validate-run",
            "--run-dir",
            "data/runs/run_1",
            "--json",
            "--strict",
        ])

        self.assertEqual(args.command, "validate-run")
        self.assertEqual(args.run_dir, "data/runs/run_1")
        self.assertTrue(args.json)
        self.assertTrue(args.strict)
```

- [ ] **Step 2: Run parser test and verify it fails**

Run:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_run_artifact_validator.ValidateRunCliParserTest
```

Expected: FAIL because `validate-run` is not defined.

- [ ] **Step 3: Add parser command**

Modify `app/main.py` in `build_parser()` after `summarize-runs`:

```python
    validate_parser = subparsers.add_parser(
        "validate-run",
        help="Validate an existing run directory for artifact integrity",
    )
    validate_parser.add_argument("--run-dir", required=True)
    validate_parser.add_argument(
        "--json",
        action="store_true",
        help="Print full validation JSON",
    )
    validate_parser.add_argument(
        "--strict",
        action="store_true",
        help="Return exit code 1 when validation status is block",
    )
```

- [ ] **Step 4: Add command handling**

Modify `app/main.py` in `main()` before `parser.error(...)`:

```python
    if args.command == "validate-run":
        import json
        from tools.run_artifact_validator import report_to_dict, validate_run_dir

        report = validate_run_dir(Path(args.run_dir), expect_completed=True)
        payload = report_to_dict(report)
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(f"run_id={report.run_id}")
            print(f"run_dir={report.run_dir}")
            print(f"validation_status={report.status}")
            print(f"validation_score={report.score}")
            print(f"blocking_issues={len(report.blocking_issues)}")
            print(f"warnings={len(report.warnings)}")
            for issue in report.blocking_issues[:5]:
                print(f"BLOCKER: {issue}")
            for warning in report.warnings[:5]:
                print(f"WARNING: {warning}")
        return 1 if args.strict and report.status == "block" else 0
```

- [ ] **Step 5: Run CLI parser test**

Run:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_run_artifact_validator.ValidateRunCliParserTest
```

Expected: test passes.

- [ ] **Step 6: Run CLI dynamically against a minimal fixture**

Use a temporary fixture through a one-line Python script:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -c "import json,tempfile,pathlib,subprocess,sys; d=pathlib.Path(tempfile.mkdtemp()); r=d/'run_1'; review=r/'artifacts'/'reviews'/'review_1.json'; evalp=r/'artifacts'/'run_evaluations'/'eval_1.json'; review.parent.mkdir(parents=True); evalp.parent.mkdir(parents=True); review.write_text('{\"review_id\":\"review_1\"}',encoding='utf-8'); evalp.write_text('{\"evaluation_id\":\"eval_1\"}',encoding='utf-8'); (r/'state.json').write_text(json.dumps({'run_id':'run_1','stage':'completed','values':{},'artifacts':{'reviews':['review_1'],'run_evaluations':['eval_1']}}),encoding='utf-8'); (r/'artifact_index.jsonl').write_text(json.dumps({'kind':'reviews','artifact_id':'review_1','path':str(review)})+'\\n'+json.dumps({'kind':'run_evaluations','artifact_id':'eval_1','path':str(evalp)})+'\\n',encoding='utf-8'); p=subprocess.run([r'D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe','-m','app.main','validate-run','--run-dir',str(r),'--strict'],cwd=r'D:\Codes\VS\research_agent_lab',text=True,capture_output=True); print(p.stdout); sys.exit(p.returncode)"
```

Expected output includes `validation_status=pass`.

---

## Task 6: Harden Validator Behavior

**Files:**
- Modify: `tests/test_run_artifact_validator.py`
- Modify: `tools/run_artifact_validator.py`

- [ ] **Step 1: Add malformed artifact tests**

Append to `RunArtifactValidatorTest`:

```python
    def test_invalid_state_json_blocks_without_crash(self):
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "runs" / "run_1"
            run_dir.mkdir(parents=True)
            (run_dir / "state.json").write_text("{bad json", encoding="utf-8")

            report = validate_run_dir(run_dir, expect_completed=True)

            self.assertEqual(report.status, "block")
            self.assertTrue(any("state.json cannot be read" in issue for issue in report.blocking_issues))

    def test_artifact_index_invalid_json_blocks(self):
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "runs" / "run_1"
            _write_json(run_dir / "state.json", {
                "run_id": "run_1",
                "stage": "completed",
                "values": {},
                "artifacts": {},
            })
            (run_dir / "artifact_index.jsonl").write_text("{bad json\n", encoding="utf-8")

            report = validate_run_dir(run_dir, expect_completed=True)

            self.assertEqual(report.status, "block")
            self.assertTrue(any("artifact_index" in issue for issue in report.blocking_issues))
```

- [ ] **Step 2: Run hardening tests**

Run:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_run_artifact_validator.RunArtifactValidatorTest
```

Expected: tests pass. If failures occur, make the validator return checks rather than raising.

---

## Task 7: Update Documentation

**Files:**
- Create: `docs/p17_dynamic_validation.md`
- Modify: `docs/project_handoff.md`
- Modify: `docs/Q&A.md`

- [ ] **Step 1: Create dynamic validation runbook**

Create `docs/p17_dynamic_validation.md`:

```markdown
# P17 Dynamic Validation Runbook

This runbook validates that a run can be inspected after completion.

Use the `video_llava` interpreter:

`D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe`

## 1. Full Unit Suite

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest discover -s tests -p test*.py
```

Expected: all tests pass.

## 2. Offline Minimal Run

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir tmp\p17_validation\offline --max-papers 1
```

Then validate the printed run directory:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main validate-run --run-dir <printed_run_dir> --strict
```

Expected: validation does not block.

## 3. Retrieval Evaluation Run

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir tmp\p17_validation\retrieval --max-papers 2 --enable-retrieval-evaluation
```

Then:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main validate-run --run-dir <printed_run_dir> --strict
```

Expected: `retrieval_evaluations` exists and validation does not block.

## 4. LLM Budget-Zero Run

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir tmp\p17_validation\llm_budget_zero --max-papers 1 --enable-llm --llm-call-budget 0
```

Then:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main validate-run --run-dir <printed_run_dir> --strict
```

Expected: no real API call is required; validation does not require successful LLM output.

## 5. Experiment Smoke Run

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir tmp\p17_validation\experiment --max-papers 1 --enable-experiments
```

Then:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main validate-run --run-dir <printed_run_dir> --strict
```

Expected: `experiment_results` and `code_patches` are present and cross-linked.

## 6. Required Real API Smoke

Run with the user-confirmed tiny budget. This is required for P17 acceptance:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir tmp\p17_validation\api --max-papers 1 --enable-llm --llm-call-budget 2 --llm-token-budget 12000
```

Then validate the printed run directory.

Expected: `llm_calls` records contain no secrets and link to debug records when debug records exist.
```

- [ ] **Step 2: Update project handoff**

Modify `docs/project_handoff.md`:

- Change first update line to:

```markdown
更新时间：2026-06-24（P17 规划/实施中）
```

- In implemented agents, add:

```markdown
`ExperimentOrchestratorAgent`（P15/P16）：内部封装 CodeWriter → experiment run → AutoDebugger → retry 循环。

`CodeWriterAgent`（P15/P16）：受 `--enable-code-writes`、Topic `ProjectSafetyPolicy`、CodeTask allowed/protected 路径约束，写入前备份并记录 CodePatch。

`AutoDebuggerAgent`（P16）：解析 traceback，构造安全上下文，调用 LLM 生成 `fix_file_contents`，写 `llm_calls` 和 `auto_debug_records`。

`RunValidationAgent`（P17）：验证 run artifact 完整性、跨 artifact 链接和 secret 泄漏风险。
```

- In tools, add:

```markdown
`tools/run_artifact_validator.py`（P17）：验证 run 目录、artifact index、state artifacts、cross-links 和 secret-like values。
```

- In commands, add:

```markdown
验证已有 run：

`D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main validate-run --run-dir data\runs\<run_id> --strict`
```

- Update test section after implementation to the new count observed from full suite.

- Move stale P15 finalization note out of "下一步" when P17 covers it.

- [ ] **Step 3: Update Q&A**

Append a new section near the operational Q&A area in `docs/Q&A.md`:

```markdown
### Q：RunEvaluationAgent 和 RunValidationAgent 有什么区别？

A：`RunEvaluationAgent` 评价一次 run 的科研和流程质量，例如文献是否足够、LLM budget 是否超限、实验结果是否解析、review 是否 pass。`RunValidationAgent` 验证 run 是否可交付复盘，例如 `state.json` 是否存在、artifact index 是否指向真实文件、`AutoDebugRecord.llm_call_id` 是否能找到对应 `llm_calls`、是否有疑似 API key 泄漏。前者回答“这个 run 是否值得继续”，后者回答“这个 run 是否可被别人复现和审查”。

### Q：如何验证一个已完成 run？

A：使用：

`D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main validate-run --run-dir data\runs\<run_id> --strict`

如果返回 `validation_status=block`，先看 `BLOCKER:` 行。常见原因是 artifact 文件缺失、cross-link 丢失或 artifact 中出现疑似 secret。
```

- [ ] **Step 4: Run docs grep checks**

Run:

```bash
cmd /c rg -n "P17|RunValidationAgent|validate-run" docs\project_handoff.md docs\Q&A.md docs\p17_dynamic_validation.md
```

Expected: all three docs contain relevant P17 references.

---

## Task 8: Dynamic Validation Commands

**Files:**
- No code file required unless failures are found.
- Evidence should be summarized in `docs/project_handoff.md` after implementation.

- [ ] **Step 1: Run full unit suite**

Run:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest discover -s tests -p test*.py
```

Expected: all tests pass.

- [ ] **Step 2: Run offline minimal smoke**

Run:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir tmp\p17_validation\offline --max-papers 1
```

Capture the printed `run_dir`.

Validate:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main validate-run --run-dir <run_dir> --strict
```

Expected: exit code 0. If status is `needs_review` but exit code is 0, record warnings and decide whether they are acceptable.

- [ ] **Step 3: Run retrieval evaluation smoke**

Run:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir tmp\p17_validation\retrieval --max-papers 2 --enable-retrieval-evaluation
```

Validate printed `run_dir` with `validate-run --strict`.

Expected: exit code 0 and `retrieval_evaluations` present in artifacts.

- [ ] **Step 4: Run LLM budget-zero smoke**

Run:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir tmp\p17_validation\llm_budget_zero --max-papers 1 --enable-llm --llm-call-budget 0
```

Validate printed `run_dir` with `validate-run --strict`.

Expected: exit code 0. There must be no real API requirement.

- [ ] **Step 5: Run experiment smoke**

Run:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir tmp\p17_validation\experiment --max-papers 1 --enable-experiments
```

Validate printed `run_dir` with `validate-run --strict`.

Expected: exit code 0, with `experiment_results` and `code_patches` present.

- [ ] **Step 6: Required real API smoke**

Run with the user-confirmed tiny budget:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir tmp\p17_validation\api --max-papers 1 --enable-llm --llm-call-budget 2 --llm-token-budget 12000
```

Validate printed `run_dir` with `validate-run --strict`.

Expected: exit code 0 or documented `needs_review` warnings, with `llm_calls` present and no secrets in artifacts. Any `block` must be fixed before P17 is marked complete. If the provider fails, document the provider error, check API config once, rerun once, and do not mark P17 complete until a real API run is validated.

---

## Task 9: Cleanup And Handoff Review

**Files:**
- Modify: `docs/project_handoff.md`

- [ ] **Step 1: Classify local temporary artifacts**

Run:

```bash
cmd /c git status --short
cmd /c dir /b tmp
```

Expected: identify local-only outputs such as `tmp/p16_offline_smoke/`, `tmp/p17_validation/`, `tmp_dynamic_audit.py`, and `.superpowers/.../state`.

- [ ] **Step 2: Do not delete automatically**

Do not delete files automatically in this task. Instead, add a short note to `docs/project_handoff.md`:

```markdown
Local validation outputs under `tmp/` are smoke evidence. Do not auto-delete them, and do not commit them unless a specific run is selected as a fixture.
```

- [ ] **Step 3: Final verification**

Run:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest discover -s tests -p test*.py
```

Expected: all tests pass.

Run:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -c "import py_compile; files=['app/main.py','workflows/factory.py','agents/run_validation_agent.py','tools/run_artifact_validator.py','schemas/run_validation.py']; [py_compile.compile(f, doraise=True) for f in files]; print('py_compile_ok', len(files))"
```

Expected: `py_compile_ok 5`.

---

## Self Review

Spec coverage:

- Schema: Task 1.
- Validator tool: Tasks 2 and 3.
- Workflow agent: Task 4.
- CLI: Task 5.
- Dynamic validation: Task 8.
- Documentation and handoff: Tasks 7 and 9.

Placeholder scan:

- No `TBD`, `TODO`, or unresolved placeholder requirements are present.
- Commands use exact paths and expected outputs.

Type consistency:

- `RunValidationCheck` and `RunValidationReport` are used consistently across schema, tool, agent, and tests.
- `validate_run_dir()` returns `RunValidationReport`.
- `report_to_dict()` returns a JSON-serializable dict.
- `RunValidationAgent.name` is `run_validation_agent`, matching workflow tests.

## Execution Handoff

Recommended execution mode for DeepSeek: implement tasks sequentially with TDD, running the specified test command after each task. The real API smoke is required for acceptance and must use the tiny capped budget in this plan.
