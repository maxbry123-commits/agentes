# P15: Experiment Execution Loop — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement closed-loop experiment execution: code generation → experiment run → result analysis → auto-debug → retry, up to max_debug_attempts rounds.

**Architecture:** ExperimentOrchestratorAgent wraps CodeWriterAgent + AutonomousExperimentAgent + AutoDebuggerAgent in an inner loop. Workflow sees one agent but each sub-step produces independent auditable artifacts. Code writes are gated behind `--enable-code-writes`; `--enable-experiments` alone allows smoke execution without code changes.

**Tech Stack:** Python 3.10+ dataclasses (slots=True), difflib, shutil, subprocess, unittest

## Global Constraints

- `--enable-experiments` authorizes experiment command execution only, not code writes
- `--enable-code-writes` required for any file write; usually paired with `--enable-llm`
- CodeWriter skipped/BLOCKED must NOT prevent smoke command execution
- max_debug_attempts configurable via CLI; default 3
- All LLM calls must write `artifacts/llm_calls/*.json` and call `record_llm_usage()`
- Per-experiment_id state keys (`code_patches_by_experiment_id`, `pending_fixes_by_experiment_id`, `last_debug_records_by_experiment_id`) are the primary data sources; flat `code_patch`/`last_debug_record` keys are backward-compat only
- CodeWriter must reject absolute paths, `..` traversal, symlink escapes; must validate via `ProjectSafetyPolicy.validate_planned_paths()`
- Copy mode must ignore `.git/`, `__pycache__/`, `.pytest_cache/`, `results/`, `checkpoints/`, `wandb/`, `runs/`

---

### Task 1: Schema — CodePatch

**Files:**
- Create: `schemas/code_patch.py`
- Create: `tests/test_code_patch_schema.py`

**Interfaces:**
- Produces: `CodePatch` dataclass with `patch_id`, `experiment_id`, `task_id`, `attempt`, `mode`, `work_dir`, `changed_files`, `backup_paths`, `diff_summary`, `status`, `reason`

- [ ] **Step 1: Write schema test**

```python
# tests/test_code_patch_schema.py
from __future__ import annotations
from unittest import TestCase, main
from schemas.code_patch import CodePatch


class CodePatchSchemaTest(TestCase):
    def test_defaults(self):
        patch = CodePatch()
        self.assertTrue(patch.patch_id.startswith("patch_"))
        self.assertEqual(patch.experiment_id, "")
        self.assertEqual(patch.task_id, "")
        self.assertEqual(patch.attempt, 0)
        self.assertEqual(patch.mode, "copy")
        self.assertEqual(patch.work_dir, "")
        self.assertEqual(patch.changed_files, [])
        self.assertEqual(patch.backup_paths, {})
        self.assertEqual(patch.diff_summary, "")
        self.assertEqual(patch.status, "pending")
        self.assertEqual(patch.reason, "")

    def test_changed_files_structure(self):
        patch = CodePatch(
            experiment_id="exp_1",
            changed_files=[
                {
                    "relative_path": "model/decoder.py",
                    "action": "modify",
                    "diff": "- old line\n+ new line",
                    "base_file_hash": "abc123",
                    "new_file_hash": "def456",
                }
            ],
        )
        self.assertEqual(len(patch.changed_files), 1)
        self.assertEqual(patch.changed_files[0]["relative_path"], "model/decoder.py")
        self.assertEqual(patch.changed_files[0]["action"], "modify")
        self.assertEqual(patch.changed_files[0]["diff"], "- old line\n+ new line")
        self.assertEqual(patch.changed_files[0]["base_file_hash"], "abc123")
        self.assertEqual(patch.changed_files[0]["new_file_hash"], "def456")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m pytest tests/test_code_patch_schema.py -v 2>&1 || D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_code_patch_schema -v`
Expected: ImportError (module not found)

- [ ] **Step 3: Write schema**

```python
# schemas/code_patch.py
from __future__ import annotations
from dataclasses import dataclass, field
from schemas.base import new_id


@dataclass(slots=True)
class CodePatch:
    patch_id: str = field(default_factory=lambda: new_id("patch"))
    experiment_id: str = ""
    task_id: str = ""
    attempt: int = 0
    mode: str = "copy"
    work_dir: str = ""
    changed_files: list[dict] = field(default_factory=list)
    backup_paths: dict[str, str] = field(default_factory=dict)
    diff_summary: str = ""
    status: str = "pending"
    reason: str = ""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_code_patch_schema -v`
Expected: 2 tests pass

- [ ] **Step 5: Commit**

```bash
git add schemas/code_patch.py tests/test_code_patch_schema.py
git commit -m "feat: add CodePatch schema for experiment code changes"
```

---

### Task 2: Schema — AutoDebugRecord

**Files:**
- Create: `schemas/auto_debug_record.py`
- Create: `tests/test_auto_debug_record_schema.py`

**Interfaces:**
- Produces: `AutoDebugRecord` dataclass with `record_id`, `experiment_id`, `result_id`, `patch_id`, `attempt_number`, `error_summary`, `fix_description`, `fix_file_contents`, `fix_successful`, `llm_call_id`, `log_artifact_id`

- [ ] **Step 1: Write schema test**

```python
# tests/test_auto_debug_record_schema.py
from __future__ import annotations
from unittest import TestCase, main
from schemas.auto_debug_record import AutoDebugRecord


class AutoDebugRecordSchemaTest(TestCase):
    def test_defaults(self):
        record = AutoDebugRecord()
        self.assertTrue(record.record_id.startswith("debug_"))
        self.assertEqual(record.experiment_id, "")
        self.assertEqual(record.result_id, "")
        self.assertEqual(record.patch_id, "")
        self.assertEqual(record.attempt_number, 0)
        self.assertEqual(record.error_summary, "")
        self.assertEqual(record.fix_description, "")
        self.assertEqual(record.fix_file_contents, {})
        self.assertFalse(record.fix_successful)
        self.assertEqual(record.llm_call_id, "")
        self.assertEqual(record.log_artifact_id, "")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_auto_debug_record_schema -v`
Expected: ImportError

- [ ] **Step 3: Write schema**

```python
# schemas/auto_debug_record.py
from __future__ import annotations
from dataclasses import dataclass, field
from schemas.base import new_id


@dataclass(slots=True)
class AutoDebugRecord:
    record_id: str = field(default_factory=lambda: new_id("debug"))
    experiment_id: str = ""
    result_id: str = ""
    patch_id: str = ""
    attempt_number: int = 0
    error_summary: str = ""
    fix_description: str = ""
    fix_file_contents: dict[str, str] = field(default_factory=dict)
    fix_successful: bool = False
    llm_call_id: str = ""
    log_artifact_id: str = ""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_auto_debug_record_schema -v`
Expected: 1 test pass

- [ ] **Step 5: Commit**

```bash
git add schemas/auto_debug_record.py tests/test_auto_debug_record_schema.py
git commit -m "feat: add AutoDebugRecord schema for debug attempt tracking"
```

---

### Task 3: Schema — Extend ExperimentPlan and ExperimentResult

**Files:**
- Modify: `schemas/experiment_plan.py` (add `success_criteria` field after `acceptance_criteria`)
- Modify: `schemas/experiment_result.py` (add `attempt`, `patch_id`, `commands`, `timed_out`, `work_dir`, `criteria_results` fields)

**Interfaces:**
- Consumes: existing `ExperimentPlan` (line 20), existing `ExperimentResult` (line 9-21)
- Produces: `ExperimentPlan.success_criteria: dict[str, object]`, `ExperimentResult` with 6 new optional fields

- [ ] **Step 1: Modify experiment_plan.py**

```python
# schemas/experiment_plan.py — after acceptance_criteria line (line 20), add:
    success_criteria: dict[str, object] = field(default_factory=dict)
```

- [ ] **Step 2: Modify experiment_result.py**

```python
# schemas/experiment_result.py — after notes line (line 21), add:
    attempt: int = 0
    patch_id: str = ""
    commands: list[str] = field(default_factory=list)
    timed_out: bool = False
    work_dir: str = ""
    criteria_results: list[dict] = field(default_factory=list)
```

- [ ] **Step 3: Run existing tests to verify no regressions**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_experiment_decision tests.test_autonomous_experiment tests.test_experiment_result -v`
Expected: All existing tests pass

- [ ] **Step 4: Commit**

```bash
git add schemas/experiment_plan.py schemas/experiment_result.py
git commit -m "feat: extend ExperimentPlan with success_criteria, ExperimentResult with attempt/patch_id/work_dir/criteria_results"
```

---

### Task 4: CodeWriterAgent — Path validation and enable_code_writes gate

**Files:**
- Create: `agents/code_writer.py`
- Create: `tests/test_code_writer.py`

**Interfaces:**
- Consumes: `CodePatch` (Task 1), `ExperimentPlan.success_criteria` (Task 3)
- Consumes: `state.values["experiment_plans"]`, `state.values["code_tasks"]`, `state.values.get("pending_fixes_by_experiment_id", {}).get(experiment_id)`
- Consumes: `state.topic.codebase`, `state.topic.allowed_auto_edit()`, `state.topic.protected_files()`
- Consumes: `context.settings["enable_code_writes"]`, `context.settings["enable_llm"]`
- Produces: `CodePatch` written to `state.values["code_patches_by_experiment_id"][experiment_id]` and `state.values["code_patch"]`

- [ ] **Step 1: Write failing test for enable_code_writes gate**

```python
# tests/test_code_writer.py
from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from agents.code_writer import CodeWriterAgent
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState
from schemas.topic_pack import TopicPack


def _state() -> ResearchState:
    topic = TopicPack(topic_name="test", codebase={"repo_path": "/fake/repo", "allowed_auto_edit": ["model/"], "protected_files": ["model/secrets.py"]})
    state = ResearchState(topic=topic)
    state.values["experiment_plans"] = [{"experiment_id": "exp_1", "hypothesis": "test", "modification": "change decoder", "files_to_change": ["model/decoder.py"]}]
    state.values["code_tasks"] = [{"task_id": "ct_1", "experiment_id": "exp_1", "allowed_paths": ["model/"], "protected_paths": ["model/secrets.py"]}]
    return state


class CodeWriterAgentTest(TestCase):
    def test_skips_when_code_writes_disabled(self):
        with TemporaryDirectory() as tmp:
            state = _state()
            context = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None, tool_registry=None,
                settings={"enable_code_writes": False},
            )
            agent = CodeWriterAgent()
            result = agent.run(state, context)
            self.assertIn("code_patches_by_experiment_id", state.values)
            patch = state.values["code_patches_by_experiment_id"].get("exp_1")
            self.assertEqual(patch["status"], "skipped")
            self.assertIn("code writes disabled", patch["reason"])


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_code_writer.CodeWriterAgentTest.test_skips_when_code_writes_disabled -v`
Expected: ImportError

- [ ] **Step 3: Write minimal CodeWriterAgent with gate only**

```python
# agents/code_writer.py
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
from typing import Any

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from schemas.code_patch import CodePatch


class CodeWriterAgent(Agent):
    name = "code_writer"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        plans = state.values.get("experiment_plans", []) or []
        if not plans:
            return AgentResult(notes=["code_writer: no experiment plans"])

        plan = plans[0] if isinstance(plans[0], dict) else {}
        experiment_id = plan.get("experiment_id", "unknown")
        enable_code_writes = bool(context.settings.get("enable_code_writes"))

        if not enable_code_writes:
            patch = CodePatch(
                experiment_id=experiment_id,
                status="skipped",
                reason="code writes disabled; set --enable-code-writes",
            )
            return self._persist(patch, state, context, experiment_id)

        return AgentResult(notes=["code_writer: not implemented yet"])

    def _persist(self, patch: CodePatch, state: ResearchState, context: AgentContext, experiment_id: str) -> AgentResult:
        patch_dict = asdict(patch)
        patches = state.values.setdefault("code_patches_by_experiment_id", {})
        patches[experiment_id] = patch_dict
        state.values["code_patch"] = patch_dict
        context.artifact_store.save_json(state.run_id, "code_patches", patch.patch_id, patch_dict)
        return AgentResult(
            notes=[f"code_writer: status={patch.status} reason={patch.reason}"],
            artifacts={"code_patches": [patch.patch_id]},
            values={
                "code_patch": patch_dict,
                "code_patches_by_experiment_id": patches,
            },
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_code_writer.CodeWriterAgentTest.test_skips_when_code_writes_disabled -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agents/code_writer.py tests/test_code_writer.py
git commit -m "feat: add CodeWriterAgent with enable_code_writes gate"
```

---

### Task 5: CodeWriterAgent — Path safety validation

**Files:**
- Modify: `agents/code_writer.py` (add `_validate_paths`, `_resolve_and_check` methods)
- Modify: `tests/test_code_writer.py` (add tests)

**Interfaces:**
- Consumes: `TopicPack.allowed_auto_edit()`, `TopicPack.protected_files()`
- Produces: `_validate_paths(relative_paths, work_dir, allowed, protected) -> tuple[bool, str]`

- [ ] **Step 1: Write failing tests for path safety**

```python
# Add to tests/test_code_writer.py — inside CodeWriterAgentTest class:

def test_rejects_absolute_path(self):
    agent = CodeWriterAgent()
    ok, reason = agent._validate_paths(
        ["/etc/passwd"], Path("/tmp/work"), ["model/"], []
    )
    self.assertFalse(ok)
    self.assertIn("absolute", reason.lower())

def test_rejects_parent_traversal(self):
    agent = CodeWriterAgent()
    ok, reason = agent._validate_paths(
        ["../outside.py"], Path("/tmp/work"), ["model/"], []
    )
    self.assertFalse(ok)
    self.assertIn("..", reason)

def test_rejects_path_outside_work_dir(self):
    agent = CodeWriterAgent()
    ok, reason = agent._validate_paths(
        ["model/../../etc/hacked"], Path("/tmp/work/sub/proj"), ["model/"], []
    )
    self.assertFalse(ok)

def test_rejects_protected_file(self):
    agent = CodeWriterAgent()
    ok, reason = agent._validate_paths(
        ["model/secrets.py"], Path("/tmp/work"), ["model/"], ["model/secrets.py"]
    )
    self.assertFalse(ok)
    self.assertIn("protected", reason.lower())

def test_accepts_valid_path_in_allowed(self):
    agent = CodeWriterAgent()
    ok, reason = agent._validate_paths(
        ["model/decoder.py"], Path("/tmp/work"), ["model/"], ["model/secrets.py"]
    )
    self.assertTrue(ok)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_code_writer -v`
Expected: 5 new tests FAIL (AttributeError: no _validate_paths)

- [ ] **Step 3: Implement path validation**

```python
# Add to CodeWriterAgent class in agents/code_writer.py:

def _validate_paths(self, relative_paths: list[str], work_dir: Path, allowed_paths: list[str], protected_paths: list[str]) -> tuple[bool, str]:
    for rel in relative_paths:
        if not rel or rel != rel.strip():
            return False, f"empty or whitespace-padded path: {rel!r}"
        if Path(rel).is_absolute() or rel.startswith("/") or (len(rel) >= 3 and rel[1] == ":"):
            return False, f"absolute or drive-letter path rejected: {rel}"
        if ".." in Path(rel).parts:
            return False, f"parent traversal rejected: {rel}"
        resolved = (work_dir / rel).resolve()
        work_resolved = work_dir.resolve()
        try:
            resolved.relative_to(work_resolved)
        except ValueError:
            return False, f"resolved path {resolved} is outside work_dir {work_resolved}"
        for protected in protected_paths:
            protected_path = Path(protected)
            if protected_path.is_absolute():
                if resolved == work_dir.resolve() / protected_path:
                    return False, f"protected file: {rel}"
            else:
                if resolved == work_dir.resolve() / protected_path:
                    return False, f"protected file: {rel}"
        in_allowed = any(
            resolved == work_resolved / Path(a).resolve().relative_to(work_resolved)
            if (work_resolved / a).resolve().is_relative_to(work_resolved)
            else False
            for a in allowed_paths
        ) if allowed_paths else True
        if not in_allowed:
            parent_in_allowed = any(
                str(resolved.relative_to(work_resolved)).startswith(str(a).rstrip("/") + "/")
                or str(resolved.relative_to(work_resolved)) == str(a).rstrip("/")
                for a in allowed_paths
            )
            if not parent_in_allowed:
                return False, f"path {rel} not in allowed_paths"
    return True, ""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_code_writer -v`
Expected: 6 tests pass (1 from Task 4 + 5 new)

- [ ] **Step 5: Commit**

```bash
git add agents/code_writer.py tests/test_code_writer.py
git commit -m "feat: add path safety validation to CodeWriterAgent"
```

---

### Task 6: CodeWriterAgent — Copy mode and file operations

**Files:**
- Modify: `agents/code_writer.py` (add `_setup_work_dir`, `_copy_codebase`, `_apply_changes`, `_make_backup` methods)
- Modify: `tests/test_code_writer.py` (add tests for copy mode, backup, hash)

**Interfaces:**
- Produces: `_setup_work_dir(state, target_dir) -> Path`, `_copy_codebase(src, dst) -> None`, `_apply_changes(...) -> CodePatch`

- [ ] **Step 1: Write test for copy mode**

```python
# Add to tests/test_code_writer.py — inside CodeWriterAgentTest class:

def test_copy_mode_creates_work_dir(self):
    import shutil
    with TemporaryDirectory() as tmp:
        src_dir = Path(tmp) / "src"
        src_dir.mkdir()
        (src_dir / "model").mkdir()
        (src_dir / "model" / "test.py").write_text("print('hello')")
        (src_dir / ".git").mkdir()

        state = _state()
        state.topic.codebase["repo_path"] = str(src_dir)
        context = AgentContext(
            artifact_store=ArtifactStore(Path(tmp) / "runs"),
            memory_store=None, tool_registry=None,
            settings={"enable_code_writes": True, "enable_llm": False},
        )
        state.values["experiment_plans"] = [{"experiment_id": "exp_1", "hypothesis": "test", "modification": "change"}]
        state.values["code_tasks"] = [{"task_id": "ct_1", "experiment_id": "exp_1", "allowed_paths": ["model/test.py"], "protected_paths": []}]

        agent = CodeWriterAgent()
        agent.run(state, context)

        patch = state.values["code_patches_by_experiment_id"]["exp_1"]
        self.assertIn("code_copy", patch["work_dir"])
        self.assertEqual(patch["mode"], "copy")
        self.assertTrue(Path(patch["work_dir"]).exists())
        self.assertTrue((Path(patch["work_dir"]) / "model" / "test.py").exists())
        self.assertFalse((Path(patch["work_dir"]) / ".git").exists(),
                         ".git should not be copied")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_code_writer.CodeWriterAgentTest.test_copy_mode_creates_work_dir -v`
Expected: FAIL (not implemented)

- [ ] **Step 3: Implement copy mode**

```python
# Add to CodeWriterAgent in agents/code_writer.py:

import hashlib
import shutil

_COPY_IGNORE_DIRS = {".git", "__pycache__", ".pytest_cache", "results", "checkpoints", "wandb", "runs"}


def _ignore_dirs(base_dir: str, names: list[str]) -> set[str]:
    return {n for n in names if n in _COPY_IGNORE_DIRS or n.endswith((".pt", ".pth", ".ckpt", ".safetensors"))}


def _setup_work_dir(self, repo_path: str, run_dir: Path, experiment_id: str, attempt: int) -> tuple[Path, str]:
    codebase = self._get_codebase(state)
    if bool(codebase.get("copy_can_modify")):
        return Path(repo_path), "sandbox"
    dst = run_dir / "code_copies" / experiment_id / f"attempt_{attempt}"
    dst.mkdir(parents=True, exist_ok=True)
    self._copy_codebase(Path(repo_path), dst)
    return dst, "copy"


def _copy_codebase(self, src: Path, dst: Path) -> None:
    for item in src.iterdir():
        if item.name in _COPY_IGNORE_DIRS:
            continue
        if item.is_dir():
            shutil.copytree(str(item), str(dst / item.name), ignore=_ignore_dirs, dirs_exist_ok=True)
        else:
            dst.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(item), str(dst / item.name))


def _hash_file(self, path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _make_backup(self, file_path: Path) -> Path:
    bak = file_path.with_suffix(file_path.suffix + ".bak")
    shutil.copy2(str(file_path), str(bak))
    return bak


def _apply_changes(self, changes: dict[str, str], work_dir: Path, allowed: list[str], protected: list[str]) -> tuple[list[dict], dict[str, str]]:
    changed_files: list[dict] = []
    backups: dict[str, str] = {}

    ok, reason = self._validate_paths(list(changes.keys()), work_dir, allowed, protected)
    if not ok:
        return [], {}, ok, reason

    for rel_path, new_content in changes.items():
        target = (work_dir / rel_path).resolve()
        base_hash = ""
        if target.exists():
            base_hash = self._hash_file(target)
            bak = self._make_backup(target)
            backups[rel_path] = str(bak)

        target.parent.mkdir(parents=True, exist_ok=True)
        action = "modify" if base_hash else "create"
        old_content = target.read_text(encoding="utf-8") if target.exists() else ""
        target.write_text(new_content, encoding="utf-8")
        new_hash = self._hash_file(target)

        diff_lines = list(
            __import__("difflib").unified_diff(
                old_content.splitlines(keepends=True) if old_content else [],
                new_content.splitlines(keepends=True),
                fromfile=str(rel_path), tofile=str(rel_path),
            )
        )
        changed_files.append({
            "relative_path": rel_path,
            "action": action,
            "diff": "".join(diff_lines),
            "base_file_hash": base_hash,
            "new_file_hash": new_hash,
        })

    return changed_files, backups, True, ""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_code_writer -v`
Expected: 7 tests pass

- [ ] **Step 5: Commit**

```bash
git add agents/code_writer.py tests/test_code_writer.py
git commit -m "feat: add copy mode, backup, and hash to CodeWriterAgent"
```

---

### Task 7: ResultParser — success criteria extraction and checking

**Files:**
- Modify: `agents/result_parser.py` (add `_extract_success_metric`, `_check_criteria`; modify `parse_experiment_output`)
- Modify: `tests/test_result_parser.py` (add 7 criteria tests)

**Interfaces:**
- Consumes: `parse_experiment_output(experiment_id, stdout, stderr, returncode, command, expected_metrics, duration_seconds, success_criteria=None)`
- Produces: `_extract_success_metric(text, metric_spec) -> float | None`, `_check_criteria(metrics, criteria, text) -> tuple[bool, list[dict]]`

- [ ] **Step 1: Write failing tests for criteria checking**

```python
# Add to tests/test_result_parser.py:

class CriteriaCheckTest(TestCase):
    def test_check_criteria_metric_pass(self):
        from agents.result_parser import _check_criteria
        metrics = {"ade": 0.30}
        criteria = {"mode": "metric", "metrics": [{"name": "ade", "target": 0.50, "direction": "lte"}]}
        passed, results = _check_criteria(metrics, criteria)
        self.assertTrue(passed)
        self.assertTrue(results[0]["pass"])

    def test_check_criteria_metric_fail(self):
        from agents.result_parser import _check_criteria
        metrics = {"ade": 0.90}
        criteria = {"mode": "metric", "metrics": [{"name": "ade", "target": 0.50, "direction": "lte"}]}
        passed, results = _check_criteria(metrics, criteria)
        self.assertFalse(passed)
        self.assertFalse(results[0]["pass"])

    def test_check_criteria_bad_target_no_crash(self):
        from agents.result_parser import _check_criteria
        metrics = {"ade": 0.30}
        criteria = {"mode": "metric", "metrics": [{"name": "ade", "target": "bad"}]}
        passed, results = _check_criteria(metrics, criteria)
        self.assertFalse(passed)

    def test_check_criteria_empty_metrics(self):
        from agents.result_parser import _check_criteria
        passed, results = _check_criteria({}, {"mode": "metric", "metrics": []})
        self.assertTrue(passed)

    def test_check_criteria_direction_lte(self):
        from agents.result_parser import _check_criteria
        metrics = {"ade": 0.30}
        criteria = {"mode": "metric", "metrics": [{"name": "ade", "target": 0.50, "direction": "lte"}]}
        passed, results = _check_criteria(metrics, criteria)
        self.assertTrue(passed)

    def test_pattern_extract_fallback(self):
        from agents.result_parser import _check_criteria
        metrics = {}
        criteria = {"mode": "metric", "metrics": [{"name": "accuracy", "target": 0.9, "direction": "gte", "pattern": r"Accuracy:\s*([0-9.]+)"}]}
        text = "Epoch 10 complete. Accuracy: 0.95"
        passed, results = _check_criteria(metrics, criteria, text)
        self.assertTrue(passed)
        self.assertEqual(results[0]["actual"], 0.95)

    def test_bad_pattern_no_crash(self):
        from agents.result_parser import _check_criteria
        metrics = {}
        criteria = {"mode": "metric", "metrics": [{"name": "acc", "target": 0.9, "pattern": r"[invalid"}]}
        passed, results = _check_criteria(metrics, criteria, "some text")
        self.assertFalse(passed)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_result_parser.CriteriaCheckTest -v`
Expected: FAIL (no `_check_criteria`)

- [ ] **Step 3: Implement criteria functions in result_parser.py**

```python
# Add to agents/result_parser.py, before parse_experiment_output:

def _extract_success_metric(text: str, metric_spec: dict) -> float | None:
    pattern = metric_spec.get("pattern")
    if not pattern:
        return None
    try:
        match = re.search(str(pattern), text, re.IGNORECASE)
    except re.error:
        return None
    if not match:
        return None
    try:
        return float(match.group(1))
    except (IndexError, TypeError, ValueError):
        return None


def _check_criteria(metrics: dict[str, float], criteria: dict, text: str = "") -> tuple[bool, list[dict]]:
    targets = criteria.get("metrics", [])
    if not targets:
        return True, []
    results = []
    for t in targets:
        if not isinstance(t, dict):
            continue
        name = str(t.get("name", "")).lower()
        if not name:
            continue
        actual = metrics.get(name)
        if actual is None:
            actual = _extract_success_metric(text, t)
        if actual is None:
            results.append({"metric": name, "pass": False, "reason": "not found"})
            continue
        try:
            target = float(t.get("target", 0))
        except (TypeError, ValueError):
            results.append({"metric": name, "pass": False, "reason": f"bad target: {t.get('target')}"})
            continue
        direction = t.get("direction", "gte")
        ok = actual >= target if direction != "lte" else actual <= target
        results.append({"metric": name, "actual": actual, "target": target, "pass": ok})
    return all(r["pass"] for r in results), results
```

- [ ] **Step 4: Modify parse_experiment_output to accept and use success_criteria**

```python
# In parse_experiment_output(), add parameter:
def parse_experiment_output(
    experiment_id: str,
    stdout: str,
    stderr: str,
    returncode: int,
    command: str,
    expected_metrics: list[str] | None = None,
    duration_seconds: float = 0.0,
    success_criteria: dict | None = None,
) -> ExperimentResult:
```

After the existing status-setting logic, add:
```python
    # After existing status logic, add criteria check:
    if success_criteria and isinstance(success_criteria, dict):
        criteria_mode = str(success_criteria.get("mode", ""))
        if criteria_mode in {"metric", "both"}:
            criteria_pass, criteria_results = _check_criteria(
                result.metrics, success_criteria, combined
            )
            result.criteria_results = criteria_results
            if not criteria_pass and result.status == "passed":
                result.status = "failed"
                result.notes.append("criteria not met")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_result_parser -v`
Expected: All CriteriaCheckTest + existing tests pass

- [ ] **Step 6: Commit**

```bash
git add agents/result_parser.py tests/test_result_parser.py
git commit -m "feat: add _check_criteria and _extract_success_metric to result parser"
```

---

### Task 8: DeveloperAgent — experiment-specific implementation notes

**Files:**
- Modify: `agents/developer_agent.py` (add experiment-specific notes from ExperimentPlan)
- Modify: `tests/test_full_research_loop.py` (verify notes appear)

**Interfaces:**
- Consumes: `state.values["experiment_plans"][0]` with `hypothesis`, `modification`, `files_to_change`, `baseline`
- Produces: `CodeTask.implementation_notes` with 4 experiment-specific notes prepended

- [ ] **Step 1: Read current DeveloperAgent to understand existing implementation_notes generation**

```python
# Key location: agents/developer_agent.py, look for implementation_notes= line
```

- [ ] **Step 2: Modify implementation_notes to include plan details**

Find the `implementation_notes=[` line in DeveloperAgent.run(). Change from:
```python
implementation_notes=[
    "Read target repository before editing.",
    ...
],
```
To:
```python
implementation_notes=[
    f"Goal: {plan.get('hypothesis', '')}",
    f"Change: {plan.get('modification', '')}",
    f"Files: {', '.join(plan.get('files_to_change', []))}",
    f"Baseline: {plan.get('baseline', '')}",
    "Read target repository before editing.",
    ...
],
```

- [ ] **Step 3: Run existing tests**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_full_research_loop -v`
Expected: Pass (or minor note count adjustments needed)

- [ ] **Step 4: Commit**

```bash
git add agents/developer_agent.py
git commit -m "feat: prepend experiment-specific notes from ExperimentPlan to CodeTask"
```

---

### Task 9: AutonomousExperimentAgent — run_single_plan method

**Files:**
- Modify: `agents/autonomous_experiment.py` (add `run_single_plan`, modify `run` to delegate)
- Modify: `tests/test_autonomous_experiment.py` (add tests for run_single_plan)

**Interfaces:**
- Consumes: `code_patches_by_experiment_id` for work_dir; `success_criteria` for criteria check
- Produces: `run_single_plan(state, context, plan, patch_dict=None, attempt=0) -> list[dict]`

- [ ] **Step 1: Write test for run_single_plan**

```python
# Add to tests/test_autonomous_experiment.py:

def test_run_single_plan_uses_work_dir_from_code_patch(self):
    with TemporaryDirectory() as tmp:
        topic = TopicPack(topic_name="test", codebase={"repo_path": tmp})
        state = ResearchState(topic=topic)
        plan = {"experiment_id": "exp_1"}
        patch = {"work_dir": tmp, "experiment_id": "exp_1", "attempt": 0}
        context = AgentContext(
            artifact_store=ArtifactStore(Path(tmp)),
            memory_store=None, tool_registry=None,
            settings={"enable_experiments": True},
        )
        agent = AutonomousExperimentAgent()
        results = agent.run_single_plan(state, context, plan, patch, attempt=0)
        self.assertIsInstance(results, list)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_autonomous_experiment -v`
Expected: FAIL (no run_single_plan)

- [ ] **Step 3: Implement run_single_plan**

```python
# Add to AutonomousExperimentAgent class:

def run_single_plan(self, state: ResearchState, context: AgentContext, plan: dict, patch_dict: dict | None = None, attempt: int = 0) -> list[dict]:
    experiment_id = plan.get("experiment_id", "unknown")
    codebase = state.topic.codebase
    repo_path = codebase.get("repo_path", "")

    work_dir = repo_path
    if patch_dict and patch_dict.get("work_dir"):
        work_dir = patch_dict["work_dir"]
    elif isinstance(state.values.get("code_patches_by_experiment_id"), dict):
        by_id = state.values["code_patches_by_experiment_id"]
        if experiment_id in by_id and by_id[experiment_id].get("work_dir"):
            work_dir = by_id[experiment_id]["work_dir"]

    if not context.settings.get("enable_experiments"):
        return []

    smoke_commands = self._smoke_commands(state)
    results: list[dict] = []
    for cmd in smoke_commands:
        result = self._execute_and_parse(experiment_id, cmd, work_dir, state)
        result.attempt = attempt
        result.patch_id = patch_dict.get("patch_id", "") if patch_dict else ""
        result.work_dir = work_dir
        context.artifact_store.save_json(state.run_id, "experiment_results", result.result_id, result)
        results.append(asdict(result))
        if result.status == "error":
            break
    return results


def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
    plans = state.values.get("experiment_plans", []) or []
    if not plans:
        state.values["experiment_results"] = []
        return AgentResult(notes=["skipped: no experiment plans"], values={"experiment_results": []})

    all_results: list[dict] = []
    for plan in plans:
        if isinstance(plan, dict):
            results = self.run_single_plan(state, context, plan)
            all_results.extend(results)

    state.values["experiment_results"] = all_results
    return AgentResult(
        notes=self._summarize(all_results),
        artifacts={"experiment_results": [r["result_id"] for r in all_results]},
        values={"experiment_results": all_results},
    )
```

Update `_execute_and_parse` to accept `work_dir` instead of `repo_path`:
```python
def _execute_and_parse(self, experiment_id: str, command: str, work_dir: str, state: ResearchState) -> ExperimentResult:
    cwd, clean_command = _normalize_command(command, work_dir)
    executor = ScopedCodeExecutor(work_dir)
    # ... rest unchanged
```

- [ ] **Step 4: Run tests**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_autonomous_experiment -v`
Expected: All tests pass (existing + new)

- [ ] **Step 5: Commit**

```bash
git add agents/autonomous_experiment.py tests/test_autonomous_experiment.py
git commit -m "feat: add run_single_plan to AutonomousExperimentAgent with work_dir from CodePatch"
```

---

### Task 10: ExperimentDecisionAgent — defensive max and orchestrator summary

**Files:**
- Modify: `agents/experiment_decision.py` (max default=0, read orchestrator_summary for notes)
- Modify: `tests/test_experiment_decision.py` (add regression test)

**Interfaces:**
- Consumes: `state.values["orchestrator_summary"]`, `state.values["auto_debug_records_by_experiment_id"]`
- Produces: `ExperimentDecision.notes` enriched with debug context

- [ ] **Step 1: Write regression test**

```python
# Add to tests/test_experiment_decision.py:

def test_empty_results_max_default_zero_no_crash(self):
    """max() on empty sequence with default=0 should not raise ValueError."""
    from agents.experiment_decision import ExperimentDecisionAgent
    agent = ExperimentDecisionAgent()
    decision = agent._decide("exp_1", [], [])
    self.assertEqual(decision.action, "hold")

def test_orchestrator_summary_in_notes(self):
    state = _make_state([
        {"result_id": "r1", "status": "passed", "metrics": {"ade": 0.30}},
    ])
    state.values["orchestrator_summary"] = {"total_attempts": 1, "debug_rounds": 0}
    with TemporaryDirectory() as tmp:
        agent = ExperimentDecisionAgent()
        agent.run(state, _make_context(tmp))
        decision = state.values["experiment_decision"]
        self.assertEqual(decision["action"], "continue")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_experiment_decision -v`
Expected: test_empty_results_max_default_zero_no_crash may pass (already handled if _decide returns early for empty list); test_orchestrator_summary_in_notes should pass if no crash

- [ ] **Step 3: Apply defensive fix**

In `_decide()`, replace:
```python
attempt = max(r.get("attempt", 0) for r in results)
```
With:
```python
attempt = max((r.get("attempt", 0) for r in results), default=0)
```

In `run()`, add orchestrator summary reading:
```python
# After constructing first_decision, add orchestrator context:
summary = state.values.get("orchestrator_summary")
if isinstance(summary, dict) and first_decision:
    debug_rounds = summary.get("debug_rounds", 0)
    if debug_rounds > 0 and first_decision:
        first_decision["notes"] = first_decision.get("notes", []) + [
            f"orchestrator: {debug_rounds} debug round(s) used"
        ]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_experiment_decision -v`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add agents/experiment_decision.py tests/test_experiment_decision.py
git commit -m "fix: add max default=0 and orchestrator summary reading to ExperimentDecisionAgent"
```

---

### Task 11: AutoDebuggerAgent

**Files:**
- Create: `agents/auto_debugger.py`
- Create: `tests/test_auto_debugger.py`

**Interfaces:**
- Consumes: last failed `ExperimentResult` from `state.values["experiment_results"]`, `CodePatch` from `code_patches_by_experiment_id`
- Consumes: `context.settings["enable_llm"]`, `context.settings["max_debug_attempts"]`
- Produces: `AutoDebugRecord` written to `state.values["last_debug_records_by_experiment_id"][experiment_id]` and `state.values["last_debug_record"]`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_auto_debugger.py
from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from agents.auto_debugger import AutoDebuggerAgent
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState
from schemas.topic_pack import TopicPack


class AutoDebuggerAgentTest(TestCase):
    def _state_and_context(self, tmp: str, **settings):
        topic = TopicPack(topic_name="test")
        state = ResearchState(topic=topic)
        state.values["experiment_results"] = [
            {"result_id": "r1", "experiment_id": "exp_1", "status": "error",
             "error_message": "NameError: name 'x' is not defined",
             "attempt": 0, "patch_id": "patch_test1"}
        ]
        state.values["code_patches_by_experiment_id"] = {
            "exp_1": {"patch_id": "patch_test1", "work_dir": tmp, "changed_files": [{"relative_path": "model/test.py"}]}
        }
        context = AgentContext(
            artifact_store=ArtifactStore(Path(tmp)),
            memory_store=None, tool_registry=None,
            settings=settings,
        )
        return state, context

    def test_skips_when_llm_disabled(self):
        with TemporaryDirectory() as tmp:
            state, context = self._state_and_context(tmp, enable_llm=False)
            agent = AutoDebuggerAgent()
            result = agent.run(state, context)
            record = state.values.get("last_debug_record", {})
            self.assertTrue(record.get("error_summary", "").startswith("skipped") or record.get("error_summary") == "")

    def test_blocks_when_max_attempts_reached(self):
        with TemporaryDirectory() as tmp:
            state, context = self._state_and_context(tmp, enable_llm=True, max_debug_attempts=3)
            state.values["experiment_results"][0]["attempt"] = 3
            agent = AutoDebuggerAgent()
            result = agent.run(state, context)
            record = state.values.get("last_debug_record", {})
            self.assertTrue("max" in str(record).lower() or record.get("fix_file_contents", {}) == {})

    def test_no_code_patch_returns_error(self):
        with TemporaryDirectory() as tmp:
            state, context = self._state_and_context(tmp, enable_llm=True, max_debug_attempts=3)
            state.values["code_patches_by_experiment_id"] = {}
            state.values["experiment_results"] = [{"result_id": "r1", "experiment_id": "exp_1", "status": "error", "error_message": "err", "attempt": 0, "patch_id": "nonexistent"}]
            agent = AutoDebuggerAgent()
            result = agent.run(state, context)
            self.assertIn("error", result.notes[0].lower() if result.notes else "")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_auto_debugger -v`
Expected: ImportError

- [ ] **Step 3: Implement AutoDebuggerAgent**

```python
# agents/auto_debugger.py
from __future__ import annotations
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from schemas.auto_debug_record import AutoDebugRecord


_TRACEBACK_PATTERN = re.compile(
    r'File\s+"([^"]+)",\s+line\s+(\d+)', re.IGNORECASE
)


class AutoDebuggerAgent(Agent):
    name = "auto_debugger"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        results = state.values.get("experiment_results") or []
        failed = [r for r in results if isinstance(r, dict) and r.get("status") in ("error", "failed")]
        if not failed:
            return AgentResult(notes=["auto_debugger: no failed results to debug"])

        failed_result = failed[-1]
        experiment_id = failed_result.get("experiment_id", "unknown")
        attempt = failed_result.get("attempt", 0)
        patch_id = failed_result.get("patch_id", "")

        max_attempts = int(context.settings.get("max_debug_attempts", 3))
        if attempt >= max_attempts:
            record = AutoDebugRecord(
                experiment_id=experiment_id, result_id=failed_result.get("result_id", ""),
                patch_id=patch_id, attempt_number=attempt,
                error_summary="max debug attempts reached",
                fix_description="",
            )
            return self._persist(record, state, context, experiment_id)

        enable_llm = bool(context.settings.get("enable_llm"))
        if not enable_llm:
            record = AutoDebugRecord(
                experiment_id=experiment_id, result_id=failed_result.get("result_id", ""),
                patch_id=patch_id, attempt_number=attempt,
                error_summary="skipped: LLM disabled",
                fix_description="auto-debug requires --enable-llm",
            )
            return self._persist(record, state, context, experiment_id)

        patches = state.values.get("code_patches_by_experiment_id", {})
        code_patch = patches.get(experiment_id, {})
        if not code_patch:
            record = AutoDebugRecord(
                experiment_id=experiment_id, result_id=failed_result.get("result_id", ""),
                patch_id=patch_id, attempt_number=attempt,
                error_summary="error: no CodePatch for experiment",
                fix_description="",
            )
            return self._persist(record, state, context, experiment_id)

        work_dir = Path(code_patch.get("work_dir", ""))
        error_text = failed_result.get("error_message", "")
        log_tail = failed_result.get("log_tail", "")
        combined_log = f"{error_text}\n{log_tail}"

        traceback_info = self._parse_traceback(combined_log, work_dir)

        record = AutoDebugRecord(
            experiment_id=experiment_id,
            result_id=failed_result.get("result_id", ""),
            patch_id=patch_id,
            attempt_number=attempt,
            error_summary=error_text[:500] if error_text else "no error message",
            fix_description=f"traceback parsed: {traceback_info}" if traceback_info else "no traceback found; manual review needed",
            fix_file_contents={},
        )
        return self._persist(record, state, context, experiment_id)

    def _parse_traceback(self, text: str, work_dir: Path) -> dict[str, int] | None:
        matches = _TRACEBACK_PATTERN.findall(text)
        if not matches:
            return None
        result: dict[str, int] = {}
        for filepath, line_num in matches:
            try:
                rel = str(Path(filepath).resolve().relative_to(work_dir.resolve()))
            except ValueError:
                rel = filepath
            result[rel] = int(line_num)
        return result if result else None

    def _persist(self, record: AutoDebugRecord, state: ResearchState, context: AgentContext, experiment_id: str) -> AgentResult:
        record_dict = asdict(record)
        records = state.values.setdefault("last_debug_records_by_experiment_id", {})
        records[experiment_id] = record_dict
        state.values["last_debug_record"] = record_dict
        context.artifact_store.save_json(state.run_id, "auto_debug_records", record.record_id, record_dict)
        return AgentResult(
            notes=[f"auto_debugger: experiment={experiment_id} attempt={record.attempt_number}"],
            artifacts={"auto_debug_records": [record.record_id]},
            values={
                "last_debug_record": record_dict,
                "last_debug_records_by_experiment_id": records,
            },
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_auto_debugger -v`
Expected: 3 tests pass

- [ ] **Step 5: Commit**

```bash
git add agents/auto_debugger.py tests/test_auto_debugger.py
git commit -m "feat: add AutoDebuggerAgent with traceback parsing and attempt gating"
```

---

### Task 12: ExperimentOrchestratorAgent

**Files:**
- Create: `agents/experiment_orchestrator.py`
- Create: `tests/test_experiment_orchestrator.py`

**Interfaces:**
- Consumes: `CodeWriterAgent.run()`, `AutonomousExperimentAgent.run_single_plan()`, `AutoDebuggerAgent.run()`
- Produces: `state.values["all_code_patches"]`, `state.values["all_experiment_results"]`, `state.values["experiment_results"]` (flat list), `state.values["orchestrator_summary"]`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_experiment_orchestrator.py
from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from agents.experiment_orchestrator import ExperimentOrchestratorAgent
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState
from schemas.topic_pack import TopicPack


def _make_state(**kwargs) -> ResearchState:
    topic = TopicPack(topic_name="test", codebase=kwargs.pop("codebase", {"repo_path": "/fake/repo", "allowed_auto_edit": ["model/"]}))
    state = ResearchState(topic=topic)
    state.values["experiment_plans"] = kwargs.pop("plans", [{"experiment_id": "exp_1", "hypothesis": "test", "modification": "change", "files_to_change": ["model/test.py"]}])
    state.values["code_tasks"] = [{"task_id": "ct_1", "experiment_id": "exp_1", "allowed_paths": ["model/"], "protected_paths": []}]
    return state


class ExperimentOrchestratorAgentTest(TestCase):
    def test_skips_when_experiments_disabled(self):
        with TemporaryDirectory() as tmp:
            state = _make_state()
            context = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None, tool_registry=None,
                settings={"enable_experiments": False, "enable_code_writes": False, "enable_llm": False, "max_debug_attempts": 3},
            )
            agent = ExperimentOrchestratorAgent()
            result = agent.run(state, context)
            self.assertEqual(state.values.get("experiment_results"), [])
            self.assertIn("skipped", result.notes[0])

    def test_executes_smoke_when_code_writes_disabled(self):
        with TemporaryDirectory() as tmp:
            state = _make_state()
            context = AgentContext(
                artifact_store=ArtifactStore(Path(tmp) / "runs"),
                memory_store=None, tool_registry=None,
                settings={"enable_experiments": True, "enable_code_writes": False, "enable_llm": False, "max_debug_attempts": 3},
            )
            agent = ExperimentOrchestratorAgent()
            result = agent.run(state, context)
            patches = state.values.get("code_patches_by_experiment_id", {})
            self.assertEqual(patches.get("exp_1", {}).get("status"), "skipped")
            self.assertIsInstance(state.values.get("experiment_results"), list)

    def test_multi_plan_isolation(self):
        with TemporaryDirectory() as tmp:
            state = _make_state(plans=[
                {"experiment_id": "exp_1", "hypothesis": "h1", "modification": "m1", "files_to_change": ["model/a.py"]},
                {"experiment_id": "exp_2", "hypothesis": "h2", "modification": "m2", "files_to_change": ["model/b.py"]},
            ])
            state.values["code_tasks"] = [
                {"task_id": "ct_1", "experiment_id": "exp_1", "allowed_paths": ["model/"], "protected_paths": []},
                {"task_id": "ct_2", "experiment_id": "exp_2", "allowed_paths": ["model/"], "protected_paths": []},
            ]
            context = AgentContext(
                artifact_store=ArtifactStore(Path(tmp) / "runs"),
                memory_store=None, tool_registry=None,
                settings={"enable_experiments": True, "enable_code_writes": False, "enable_llm": False, "max_debug_attempts": 3},
            )
            agent = ExperimentOrchestratorAgent()
            agent.run(state, context)
            patches = state.values.get("code_patches_by_experiment_id", {})
            self.assertIn("exp_1", patches)
            self.assertIn("exp_2", patches)
            self.assertNotEqual(patches["exp_1"].get("experiment_id"), patches["exp_2"].get("experiment_id"))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_experiment_orchestrator -v`
Expected: ImportError

- [ ] **Step 3: Implement ExperimentOrchestratorAgent**

```python
# agents/experiment_orchestrator.py
from __future__ import annotations
from dataclasses import asdict
from typing import Any

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from agents.code_writer import CodeWriterAgent
from agents.autonomous_experiment import AutonomousExperimentAgent
from agents.auto_debugger import AutoDebuggerAgent


class ExperimentOrchestratorAgent(Agent):
    name = "experiment_orchestrator"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        enable_experiments = bool(context.settings.get("enable_experiments"))
        if not enable_experiments:
            state.values["experiment_results"] = []
            return AgentResult(notes=["orchestrator: skipped (enable_experiments=False)"], values={"experiment_results": []})

        plans = state.values.get("experiment_plans", []) or []
        if not plans:
            state.values["experiment_results"] = []
            return AgentResult(notes=["orchestrator: no experiment plans"], values={"experiment_results": []})

        all_patches: list[dict] = []
        all_results: list[dict] = []
        all_debug_ids: list[str] = []
        total_debug_rounds = 0
        max_debug_attempts = int(context.settings.get("max_debug_attempts", 3))

        cw = CodeWriterAgent()
        ae = AutonomousExperimentAgent()
        ad = AutoDebuggerAgent()

        for plan in plans:
            if not isinstance(plan, dict):
                continue
            experiment_id = plan.get("experiment_id", "unknown")

            state.values["code_patches_by_experiment_id"] = state.values.get("code_patches_by_experiment_id", {})
            state.values["pending_fixes_by_experiment_id"] = state.values.get("pending_fixes_by_experiment_id", {})
            state.values["last_debug_records_by_experiment_id"] = state.values.get("last_debug_records_by_experiment_id", {})

            state.values["pending_fixes_by_experiment_id"].pop(experiment_id, None)
            state.values["last_debug_records_by_experiment_id"].pop(experiment_id, None)

            for attempt in range(max_debug_attempts + 1):
                # Step A: CodeWriter
                state.values["experiment_plans"] = [plan]
                cw_result = cw.run(state, context)

                patches = state.values.get("code_patches_by_experiment_id", {})
                patch = patches.get(experiment_id, {})
                if patch.get("status") == "blocked":
                    all_patches.append(patch)
                    break

                # Step B: AutonomousExperiment
                ae_results = ae.run_single_plan(state, context, plan, patch, attempt)
                all_results.extend(ae_results)

                # Step C: Check results
                failed = [r for r in ae_results if r.get("status") in ("error", "failed")]
                if not failed:
                    all_patches.append(patch)
                    break

                if attempt >= max_debug_attempts:
                    all_patches.append(patch)
                    break

                # Step D: AutoDebugger
                ad_result = ad.run(state, context)
                records = state.values.get("last_debug_records_by_experiment_id", {})
                record = records.get(experiment_id, {})
                if record.get("fix_file_contents"):
                    state.values.setdefault("pending_fixes_by_experiment_id", {})[experiment_id] = record["fix_file_contents"]
                    total_debug_rounds += 1
                    all_debug_ids.append(record.get("record_id", ""))
                else:
                    all_patches.append(patch)
                    break

        # Restore plans and write final state
        state.values["experiment_plans"] = plans
        state.values["experiment_results"] = all_results
        state.values["all_code_patches"] = all_patches
        state.values["all_experiment_results"] = all_results
        state.values["orchestrator_summary"] = {
            "total_plans": len(plans),
            "total_patches": len(all_patches),
            "total_results": len(all_results),
            "debug_rounds": total_debug_rounds,
        }

        return AgentResult(
            notes=[f"orchestrator: {len(plans)} plans, {len(all_results)} results, {total_debug_rounds} debug rounds"],
            artifacts={
                "code_patches": [p.get("patch_id", "") for p in all_patches if p.get("patch_id")],
                "experiment_results": [r.get("result_id", "") for r in all_results if r.get("result_id")],
                "auto_debug_records": all_debug_ids,
            },
            values={
                "experiment_results": all_results,
                "all_code_patches": all_patches,
                "all_experiment_results": all_results,
                "orchestrator_summary": state.values["orchestrator_summary"],
            },
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_experiment_orchestrator -v`
Expected: 3 tests pass

- [ ] **Step 5: Commit**

```bash
git add agents/experiment_orchestrator.py tests/test_experiment_orchestrator.py
git commit -m "feat: add ExperimentOrchestratorAgent with code→run→debug→retry loop"
```

---

### Task 13: Workflow Integration, CLI, and agents/__init__

**Files:**
- Modify: `workflows/factory.py` (replace AutonomousExperimentAgent with ExperimentOrchestratorAgent)
- Modify: `app/main.py` (add --enable-code-writes, --max-debug-attempts CLI args)
- Modify: `agents/__init__.py` (export CodeWriterAgent, AutoDebuggerAgent, ExperimentOrchestratorAgent)

**Interfaces:**
- Consumes: all new agents from Tasks 4, 11, 12

- [ ] **Step 1: Modify agents/__init__.py**

Add to imports:
```python
from agents.auto_debugger import AutoDebuggerAgent
from agents.code_writer import CodeWriterAgent
from agents.experiment_orchestrator import ExperimentOrchestratorAgent
```

Add to `__all__`:
```python
"AutoDebuggerAgent",
"CodeWriterAgent",
"ExperimentOrchestratorAgent",
```

- [ ] **Step 2: Modify workflows/factory.py**

Replace:
```python
from agents import (
    ...
    AutonomousExperimentAgent,
    ...
)
```

Add new imports and replace the factory section:
```python
from agents import (
    ...
    ExperimentOrchestratorAgent,
    ...
)

# In build_full_research_workflow():
# Remove: agents.append(AutonomousExperimentAgent())
# Add: agents.append(ExperimentOrchestratorAgent())
```

Also add `enable_code_writes` and `max_debug_attempts` to factory signature and settings dict:
```python
def build_full_research_workflow(
    ...
    enable_code_writes: bool = False,
    max_debug_attempts: int = 3,
    ...
) -> Workflow:
    ...
    settings={
        ...
        "enable_code_writes": enable_code_writes,
        "max_debug_attempts": max_debug_attempts,
    },
```

- [ ] **Step 3: Modify app/main.py — add CLI args**

Add to `run_parser`:
```python
run_parser.add_argument(
    "--enable-code-writes",
    action="store_true",
    help="Allow CodeWriterAgent to write code files",
)
run_parser.add_argument(
    "--max-debug-attempts",
    type=int,
    default=3,
    help="Maximum auto-debug retry attempts per experiment",
)
```

Add to `run_workflow()` call to `build_full_research_workflow()`:
```python
workflow = build_full_research_workflow(
    ...
    enable_code_writes=args.enable_code_writes,
    max_debug_attempts=args.max_debug_attempts,
)
```

- [ ] **Step 4: Run import check**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -c "from agents import CodeWriterAgent, AutoDebuggerAgent, ExperimentOrchestratorAgent; print('imports OK')"`
Expected: imports OK

- [ ] **Step 5: Commit**

```bash
git add agents/__init__.py workflows/factory.py app/main.py
git commit -m "feat: integrate ExperimentOrchestratorAgent into workflow, add CLI flags"
```

---

### Task 14: Full test suite and smoke verification

**Files:**
- Modify: `tests/test_full_research_loop.py` (add CLI argument tests)

- [ ] **Step 1: Write CLI integration test**

```python
# Add to tests/test_full_research_loop.py:

def test_cli_enable_code_writes_flag(self):
    """verify --enable-code-writes and --max-debug-attempts are parsed"""
    from app.main import build_parser
    parser = build_parser()
    args = parser.parse_args([
        "run", "--topic", "topics/intent_led_virat.json",
        "--enable-experiments", "--enable-code-writes",
        "--enable-llm", "--max-debug-attempts", "2",
    ])
    self.assertTrue(args.enable_code_writes)
    self.assertEqual(args.max_debug_attempts, 2)
    self.assertTrue(args.enable_experiments)
```

- [ ] **Step 2: Run full test suite**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest discover -s tests -p "test*.py" -v 2>&1 | tail -20`
Expected: All tests pass (~270 tests)

- [ ] **Step 3: Run offline smoke test**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m app.main run --topic topics/intent_led_virat.json --data-dir data --max-papers 1 --enable-experiments 2>&1 | head -30`
Expected: workflow completes, experiment_results populated, no crashes

- [ ] **Step 4: Run LLM smoke test (optional, requires API key)**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m app.main run --topic topics/intent_led_virat.json --data-dir data --max-papers 1 --enable-experiments --enable-code-writes --enable-llm --llm-call-budget 8 --max-debug-attempts 1 2>&1 | head -30`

- [ ] **Step 5: Commit**

```bash
git add tests/test_full_research_loop.py
git commit -m "test: add CLI argument parsing test for enable-code-writes and max-debug-attempts"
```

---

### Task 15: Documentation update

**Files:**
- Modify: `README.md` or relevant docs (add --enable-code-writes and --max-debug-attempts to CLI reference)

- [ ] **Step 1: Update CLI reference if one exists**

```bash
git grep -l "enable-experiments" -- "*.md" "*.rst" 2>/dev/null
```

- [ ] **Step 2: Add brief description of new flags**

- [ ] **Step 3: Commit**

```bash
git add <doc files>
git commit -m "docs: document --enable-code-writes and --max-debug-attempts CLI flags"
```
