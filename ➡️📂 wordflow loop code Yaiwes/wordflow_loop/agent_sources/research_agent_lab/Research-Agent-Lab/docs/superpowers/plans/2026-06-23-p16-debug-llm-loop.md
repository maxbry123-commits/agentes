# P16: AutoDebugger LLM 链路 + CodeWriter 安全补强 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 补全 AutoDebugger LLM 修复生成链路 + CodeWriter 接入 ProjectSafetyPolicy + CodeTask 精确匹配

**Architecture:** 修改 `agents/auto_debugger.py`（新增 _read_file_contexts、_build_debug_prompt、_write_llm_call_artifact，改造 _parse_traceback 和 run）+ `agents/code_writer.py`（policy 集成 + CodeTask 匹配）。测试用 `unittest.mock.patch` mock OpenAICompatibleClient.chat。

**Tech Stack:** Python 3.10, unittest, unittest.mock, difflib（已有）

## Global Constraints

- 复用 paper_triage flash 路由，不新增 LLM route
- 修复只覆盖 <=800 行的文件；大文件标记 read_only_context
- _parse_traceback 丢弃非 work_dir 路径，记录到 ignored_traceback_paths
- 每次 LLM 决策都写 artifacts/llm_calls/*.json
- CodeTask 缺失时 fail closed（blocked），不回退 {}
- 不新增 P15 之外的 CLI 参数
- 不修改 schema、orchestrator 循环、OpenAICompatibleClient/ModelRouter/llm_budget
- TDD：test → fail → implement → pass → commit

---

## File Structure

| 文件 | 操作 | 职责 |
|------|------|------|
| `agents/auto_debugger.py` | Modify | LLM chain: _parse_traceback 严格过滤, _read_file_contexts, _build_debug_prompt, _write_llm_call_artifact, run() 改造 |
| `agents/code_writer.py` | Modify | ProjectSafetyPolicy 集成, CodeTask experiment_id 匹配 |
| `tests/test_auto_debugger.py` | Modify | 新增 7 个测试 |
| `tests/test_code_writer.py` | Modify | 新增 4 个测试 |
| `docs/Q&A.md` | Modify | 更新 AutoDebugger 描述 |

---

### Task 1: Fix _parse_traceback() 严格过滤外部路径

**Files:**
- Modify: `agents/auto_debugger.py:80-91`
- Test: `tests/test_auto_debugger.py`

**Interfaces:**
- Consumes: `_TRACEBACK_PATTERN` (existing re.Pattern), `work_dir` (Path)
- Produces: `_parse_traceback(text, work_dir) -> tuple[dict[str, int] | None, list[str]]`
  - First element: resolved relative paths -> line numbers (None if no matches)
  - Second element: list of ignored absolute/outside paths

- [ ] **Step 1: Write failing test**

```python
def test_discards_traceback_outside_work_dir(self):
    from pathlib import Path
    with TemporaryDirectory() as tmp:
        work = Path(tmp) / "code"
        work.mkdir()
        (work / "train.py").write_text("x = 1")
        state, context = self._state_and_context(
            tmp, enable_llm=True, max_debug_attempts=2,
        )
        agent = AutoDebuggerAgent()
        text = (
            'File "/etc/system.py", line 42, in run\n'
            'File "train.py", line 10, in forward\n'
        )
        resolved, ignored = agent._parse_traceback(text, work)
        self.assertIsNotNone(resolved)
        self.assertIn("train.py", resolved)
        self.assertEqual(resolved["train.py"], 10)
        self.assertNotIn("/etc/system.py", resolved)
        self.assertNotIn("system.py", resolved)
        self.assertTrue(len(ignored) >= 1)
        self.assertTrue(any("system" in p for p in ignored))
```

- [ ] **Step 2: Run test to verify it fails**

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_auto_debugger.AutoDebuggerAgentTest.test_discards_traceback_outside_work_dir -v
```

Expected: FAIL — `ValueError: too many values to unpack` (old method returns single value)

- [ ] **Step 3: Implement fix**

Replace `_parse_traceback()` in `agents/auto_debugger.py:80-91`:

```python
def _parse_traceback(self, text: str, work_dir: Path) -> tuple[dict[str, int] | None, list[str]]:
    matches = _TRACEBACK_PATTERN.findall(text)
    if not matches:
        return None, []
    result: dict[str, int] = {}
    ignored: list[str] = []
    work_resolved = work_dir.resolve()
    for filepath, line_num in matches:
        try:
            resolved = Path(filepath).resolve()
            rel = str(resolved.relative_to(work_resolved))
            result[rel] = int(line_num)
        except ValueError:
            ignored.append(filepath)
    return (result if result else None, ignored)
```

- [ ] **Step 4: Update all existing callers — `run()` line 67**

Replace:
```python
traceback_info = self._parse_traceback(combined_log, work_dir)
```
With:
```python
traceback_info, ignored_paths = self._parse_traceback(combined_log, work_dir)
```

And add `ignored_traceback_paths=ignored_paths` to the record construction at line 69-78. Change:
```python
record = AutoDebugRecord(
    experiment_id=experiment_id,
    result_id=failed_result.get("result_id", ""),
    patch_id=patch_id,
    attempt_number=attempt,
    error_summary=error_text[:500] if error_text else "no error message",
    fix_description=f"traceback parsed: {traceback_info}" if traceback_info else "no traceback found; manual review needed",
    fix_file_contents={},
)
```
To:
```python
record = AutoDebugRecord(
    experiment_id=experiment_id,
    result_id=failed_result.get("result_id", ""),
    patch_id=patch_id,
    attempt_number=attempt,
    error_summary=error_text[:500] if error_text else "no error message",
    fix_description=f"traceback parsed: {traceback_info}" if traceback_info else "no traceback found; manual review needed",
    fix_file_contents={},
)
state.values["ignored_traceback_paths"] = ignored_paths
```

- [ ] **Step 5: Run test and existing tests to verify pass**

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_auto_debugger -v
```

Expected: 4 tests PASS (3 existing + 1 new)

- [ ] **Step 6: Commit**

```bash
git add agents/auto_debugger.py tests/test_auto_debugger.py
git commit -m "fix: _parse_traceback discards non-work_dir paths, records ignored"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```

---

### Task 2: Add _read_file_contexts() with safe truncation

**Files:**
- Modify: `agents/auto_debugger.py` (new method)
- Test: `tests/test_auto_debugger.py`

**Interfaces:**
- Consumes: candidate files list (from traceback + plan + patch), work_dir (Path)
- Produces: `_read_file_contexts(candidates, work_dir) -> tuple[dict[str, str], set[str]]`
  - First: `{relative_path: file_content}` for files that exist
  - Second: `set[str]` of `read_only_context` paths (files >800 lines)

- [ ] **Step 1: Write failing test**

```python
def test_large_file_is_read_only_context(self):
    from pathlib import Path
    with TemporaryDirectory() as tmp:
        work = Path(tmp) / "code"
        work.mkdir()
        small = work / "small.py"
        small.write_text("line\n" * 100)
        large = work / "large.py"
        large.write_text("line\n" * 900)
        agent = AutoDebuggerAgent()
        candidates = ["small.py", "large.py"]
        contexts, read_only = agent._read_file_contexts(candidates, work)
        self.assertIn("small.py", contexts)
        self.assertGreater(len(contexts["small.py"]), 0)
        self.assertIn("large.py", read_only)
        # large.py content should be truncated, not full
        self.assertLess(len(contexts.get("large.py", "").splitlines()), 900)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_auto_debugger.AutoDebuggerAgentTest.test_large_file_is_read_only_context -v
```

Expected: FAIL — AttributeError: '_read_file_contexts' not found

- [ ] **Step 3: Implement _read_file_contexts**

Add new method to `AutoDebuggerAgent` (after `_parse_traceback`, before `_persist`):

```python
_MAX_FULL_FILE_LINES = 800
_TRUNCATION_CONTEXT_LINES = 100

def _read_file_contexts(self, candidates: list[str], work_dir: Path, traceback_lines: dict[str, int] | None) -> tuple[dict[str, str], set[str]]:
    """Read candidate files. Returns (contexts, read_only_paths).
    Files > _MAX_FULL_FILE_LINES lines are truncated around error lines
    and marked as read_only_context.
    """
    contexts: dict[str, str] = {}
    read_only: set[str] = set()
    for rel_path in candidates:
        target = work_dir / rel_path
        if not target.exists() or not target.is_file():
            continue
        lines = target.read_text(encoding="utf-8").splitlines()
        if len(lines) <= _MAX_FULL_FILE_LINES:
            contexts[rel_path] = "\n".join(lines)
        else:
            read_only.add(rel_path)
            err_line = (traceback_lines or {}).get(rel_path, 1)
            start = max(0, err_line - _TRUNCATION_CONTEXT_LINES - 1)
            end = min(len(lines), err_line + _TRUNCATION_CONTEXT_LINES)
            snippet = lines[start:end]
            contexts[rel_path] = (
                f"[... {start} lines truncated ...]\n"
                + "\n".join(snippet)
                + f"\n[... {len(lines) - end} lines truncated ...]"
            )
    return contexts, read_only
```

- [ ] **Step 4: Add test for traceback+plan context reading**

```python
def test_reads_traceback_and_plan_contexts(self):
    from pathlib import Path
    with TemporaryDirectory() as tmp:
        work = Path(tmp) / "code"
        work.mkdir()
        (work / "train.py").write_text("def train():\n    pass\n")
        (work / "model.py").write_text("class Model:\n    pass\n")
        agent = AutoDebuggerAgent()
        candidates = ["train.py", "model.py"]
        traceback_lines = {"train.py": 2}
        contexts, read_only = agent._read_file_contexts(candidates, work, traceback_lines)
        self.assertIn("train.py", contexts)
        self.assertIn("model.py", contexts)
        self.assertEqual(len(read_only), 0)
```

- [ ] **Step 5: Run tests to verify pass**

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_auto_debugger -v
```

Expected: 6 tests PASS

- [ ] **Step 6: Commit**

```bash
git add agents/auto_debugger.py tests/test_auto_debugger.py
git commit -m "feat: add _read_file_contexts with safe truncation for large files"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```

---

### Task 3: Add _build_debug_prompt() and _write_llm_call_artifact()

**Files:**
- Modify: `agents/auto_debugger.py` (new methods)
- Test: `tests/test_auto_debugger.py`

**Interfaces:**
- Consumes: plan dict, failed_result dict, patch dict, file contexts dict, experiment_id, attempt
- Produces:
  - `_build_debug_prompt(...) -> list[dict[str, str]]` — messages for LLM
  - `_write_llm_call_artifact(state, context, call_data) -> None`
  - `_new_llm_call_id() -> str`

- [ ] **Step 1: Write failing tests**

```python
def test_build_debug_prompt_includes_all_sections(self):
    agent = AutoDebuggerAgent()
    plan = {"experiment_id": "exp_1", "hypothesis": "test hypothesis",
            "modification": "change x to y", "files_to_change": ["model.py"]}
    failed = {"result_id": "r1", "status": "error",
              "error_message": "NameError: x not defined",
              "log_tail": "Traceback...", "run_command": "python train.py"}
    patch = {"patch_id": "p1", "changed_files": [{"relative_path": "model.py"}]}
    contexts = {"model.py": "class Model:\n    x = 1\n"}
    messages = agent._build_debug_prompt("exp_1", 0, plan, failed, patch, contexts)
    user_content = messages[1]["content"]
    self.assertIn("test hypothesis", user_content)
    self.assertIn("change x to y", user_content)
    self.assertIn("NameError", user_content)
    self.assertIn("class Model:", user_content)


def test_llm_call_artifact_written(self):
    from pathlib import Path
    with TemporaryDirectory() as tmp:
        store = ArtifactStore(Path(tmp))
        state, _ = self._state_and_context(tmp, enable_llm=True)
        agent = AutoDebuggerAgent()
        call_data = {
            "agent": "auto_debugger",
            "experiment_id": "exp_1",
            "result_id": "r1",
            "patch_id": "p1",
            "status": "skipped_call_budget",
            "provider": "deepseek",
            "model": "deepseek-v4-flash",
            "route_enabled": True,
            "usage": {},
            "error": "",
        }
        agent._write_llm_call_artifact(state, store, call_data)
        paths = store.list_artifacts(state.run_id, "llm_calls")
        self.assertTrue(len(paths) >= 1)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_auto_debugger.AutoDebuggerAgentTest.test_build_debug_prompt_includes_all_sections tests.test_auto_debugger.AutoDebuggerAgentTest.test_llm_call_artifact_written -v
```

Expected: FAIL — AttributeError

- [ ] **Step 3: Implement methods**

Add to `AutoDebuggerAgent`, after `_read_file_contexts`:

```python
def _build_debug_prompt(
    self, experiment_id: str, attempt: int,
    plan: dict, failed: dict, patch: dict,
    contexts: dict[str, str],
) -> list[dict[str, str]]:
    topic_keywords = ", ".join(
        plan.get("files_to_change", [])[:10]
    )
    context_text = "\n\n".join(
        f"--- {path} ---\n{content}"
        for path, content in contexts.items()
    )
    return [
        {"role": "system", "content": (
            "You are debugging a failed experiment. Your job is to analyze the error "
            "and propose a minimal, safe fix that preserves the experiment's intent. "
            "Return exactly one JSON object with 'fix_description' (string) and "
            "'fix_file_contents' (dict mapping relative path to complete corrected file content). "
            "Only return files among the provided file contexts. "
            "If a file is marked as read_only_context in the prompt, do NOT include it "
            "in fix_file_contents — set its value to null instead. "
            "Keep fixes minimal: change only what's needed to resolve the error."
        )},
        {"role": "user", "content": (
            f"Experiment: {experiment_id} (attempt {attempt})\n"
            f"Hypothesis: {plan.get('hypothesis', 'unknown')}\n"
            f"Modification: {plan.get('modification', 'unknown')}\n"
            f"Files to change: {', '.join(plan.get('files_to_change', []))}\n"
            f"Keywords: {topic_keywords}\n\n"
            f"Error: {failed.get('error_message', '')}\n"
            f"Status: {failed.get('status', '')}\n"
            f"Command: {failed.get('run_command', '')}\n"
            f"Log tail:\n{failed.get('log_tail', '')}\n\n"
            f"File contexts:\n{context_text}"
        )},
    ]

def _new_llm_call_id(self) -> str:
    import uuid
    return f"llm_call_{uuid.uuid4().hex[:12]}"

def _write_llm_call_artifact(self, state, artifact_store, call_data: dict):
    call_id = self._new_llm_call_id()
    artifact_store.save_json(state.run_id, "llm_calls", call_id, call_data)
```

- [ ] **Step 4: Run tests to verify pass**

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_auto_debugger -v
```

Expected: 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add agents/auto_debugger.py tests/test_auto_debugger.py
git commit -m "feat: add _build_debug_prompt and _write_llm_call_artifact"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```

---

### Task 4: Wire LLM call flow into run()

**Files:**
- Modify: `agents/auto_debugger.py` (run method, after line 67)
- Test: `tests/test_auto_debugger.py`

**Interfaces:**
- Consumes: `_build_debug_prompt`, `_read_file_contexts`, `_write_llm_call_artifact`, `_parse_traceback`, `OpenAICompatibleClient`, `ModelRouter`, `llm_budget_allows`, `record_llm_usage`, `extract_json_object`
- Produces: Modified `run()` that may set `fix_file_contents`

- [ ] **Step 1: Write failing tests**

```python
def test_budget_exhausted_records_llm_call(self):
    from pathlib import Path
    with TemporaryDirectory() as tmp:
        state, context = self._state_and_context(
            tmp, enable_llm=True, max_debug_attempts=2,
            llm_call_budget=5, llm_token_budget=10000,
        )
        state.values["llm_calls_used"] = 5  # budget exhausted
        agent = AutoDebuggerAgent()
        result = agent.run(state, context)
        paths = context.artifact_store.list_artifacts(state.run_id, "llm_calls")
        self.assertTrue(len(paths) >= 1)
        record = state.values.get("last_debug_record", {})
        self.assertEqual(record.get("fix_file_contents", {}), {})


def test_route_disabled_records_llm_call(self):
    from pathlib import Path
    from unittest.mock import patch
    with TemporaryDirectory() as tmp:
        state, context = self._state_and_context(
            tmp, enable_llm=True, max_debug_attempts=2,
            llm_call_budget=10, llm_token_budget=50000,
        )
        # Route disabled: provider is offline
        with patch("agents.auto_debugger.ModelRouter") as mock_router:
            mock_router.return_value.route_for.return_value.provider = "offline"
            agent = AutoDebuggerAgent()
            result = agent.run(state, context)
        paths = context.artifact_store.list_artifacts(state.run_id, "llm_calls")
        self.assertTrue(len(paths) >= 1)


def test_valid_json_sets_fix_file_contents(self):
    from pathlib import Path
    from unittest.mock import patch
    from tools.llm_client import LLMResponse
    with TemporaryDirectory() as tmp:
        work = Path(tmp) / "code"
        work.mkdir()
        (work / "model.py").write_text("class Model:\n    x = missing_var\n")
        state, context = self._state_and_context(
            tmp, enable_llm=True, max_debug_attempts=2,
            llm_call_budget=10, llm_token_budget=50000,
        )
        state.values["code_patches_by_experiment_id"]["exp_1"]["work_dir"] = str(work)
        state.values["code_patches_by_experiment_id"]["exp_1"]["changed_files"] = [
            {"relative_path": "model.py"}
        ]
        state.values["experiment_plans"] = [{
            "experiment_id": "exp_1",
            "hypothesis": "test", "modification": "test",
            "files_to_change": ["model.py"],
        }]
        mock_response = LLMResponse(
            ok=True, text='{"fix_description":"add missing import","fix_file_contents":{"model.py":"class Model:\\n    x = 1\\n"}}',
            provider="deepseek", model="deepseek-v4-flash",
        )
        with patch.object(agent := AutoDebuggerAgent(), "llm_client") as mock_client:
            mock_client.chat.return_value = mock_response
            from tools.model_router import ModelRoute
            mock_router = patch("agents.auto_debugger.ModelRouter")
            mock_router.return_value.route_for.return_value = ModelRoute(
                agent="paper_triage", provider="deepseek",
                model="deepseek-v4-flash", api_key_env="DEEPSEEK_API_KEY",
                enabled=True,
            )
            mock_router.start()
            try:
                result = agent.run(state, context)
            finally:
                mock_router.stop()
        record = state.values.get("last_debug_record", {})
        self.assertIsNotNone(record.get("fix_file_contents"))
        self.assertIn("model.py", record.get("fix_file_contents", {}))
        self.assertIn("class Model:", record["fix_file_contents"]["model.py"])


def test_invalid_json_records_llm_call(self):
    from pathlib import Path
    from unittest.mock import patch
    from tools.llm_client import LLMResponse
    with TemporaryDirectory() as tmp:
        work = Path(tmp) / "code"
        work.mkdir()
        (work / "model.py").write_text("class Model:\n    x = 1\n")
        state, context = self._state_and_context(
            tmp, enable_llm=True, max_debug_attempts=2,
            llm_call_budget=10, llm_token_budget=50000,
        )
        state.values["code_patches_by_experiment_id"]["exp_1"]["work_dir"] = str(work)
        state.values["code_patches_by_experiment_id"]["exp_1"]["changed_files"] = [
            {"relative_path": "model.py"}
        ]
        state.values["experiment_plans"] = [{
            "experiment_id": "exp_1",
            "hypothesis": "test", "modification": "test",
            "files_to_change": ["model.py"],
        }]
        mock_response = LLMResponse(
            ok=True, text="not valid json {{{",
            provider="deepseek", model="deepseek-v4-flash",
        )
        with patch.object(agent := AutoDebuggerAgent(), "llm_client") as mock_client:
            mock_client.chat.return_value = mock_response
            mock_router = patch("agents.auto_debugger.ModelRouter")
            mock_router.return_value.route_for.return_value = type("obj", (), {
                "provider": "deepseek", "model": "deepseek-v4-flash",
                "enabled": True, "api_key_env": "DEEPSEEK_API_KEY",
            })()
            mock_router.start()
            try:
                result = agent.run(state, context)
            finally:
                mock_router.stop()
        paths = context.artifact_store.list_artifacts(state.run_id, "llm_calls")
        self.assertTrue(len(paths) >= 1)
        record = state.values.get("last_debug_record", {})
        self.assertEqual(record.get("fix_file_contents", {}), {})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_auto_debugger.AutoDebuggerAgentTest.test_budget_exhausted_records_llm_call tests.test_auto_debugger.AutoDebuggerAgentTest.test_route_disabled_records_llm_call tests.test_auto_debugger.AutoDebuggerAgentTest.test_valid_json_sets_fix_file_contents tests.test_auto_debugger.AutoDebuggerAgentTest.test_invalid_json_records_llm_call -v
```

Expected: FAIL — assertions fail (no llm_calls written, fix_file_contents still {})

- [ ] **Step 3: Implement full LLM flow in run()**

Replace the section from `work_dir = Path(...)` through `_persist()` (lines 62-78) in `agents/auto_debugger.py`:

```python
work_dir = Path(code_patch.get("work_dir", ""))
error_text = failed_result.get("error_message", "")
log_tail = failed_result.get("log_tail", "")
combined_log = f"{error_text}\n{log_tail}"

traceback_info, ignored_paths = self._parse_traceback(combined_log, work_dir)
state.values["ignored_traceback_paths"] = ignored_paths

# --- LLM path ---
if traceback_info is None and not plan.get("files_to_change"):
    record = AutoDebugRecord(
        experiment_id=experiment_id,
        result_id=failed_result.get("result_id", ""),
        patch_id=patch_id,
        attempt_number=attempt,
        error_summary=error_text[:500] if error_text else "no error message",
        fix_description="no traceback or actionable files; LLM skipped",
        fix_file_contents={},
    )
    return self._persist(record, state, context, experiment_id)

# Collect candidate files
plan_files = plan.get("files_to_change", [])
patch_files = [f.get("relative_path", "") for f in code_patch.get("changed_files", [])]
traceback_files = list(traceback_info.keys()) if traceback_info else []
candidates = list(dict.fromkeys(traceback_files + plan_files + patch_files))  # dedup, preserve order

contexts, read_only = self._read_file_contexts(candidates, work_dir, traceback_info or {})

# Look up route early (used by both budget and LLM call branches)
route = ModelRouter(state.topic).route_for("paper_triage")

# Check budget
allowed, budget_reason = llm_budget_allows(state, context.settings)
if not allowed:
    self._write_llm_call_artifact(state, context.artifact_store, {
        "agent": "auto_debugger",
        "experiment_id": experiment_id,
        "result_id": failed_result.get("result_id", ""),
        "patch_id": patch_id,
        "status": budget_reason,
        "provider": route.provider,
        "model": route.model,
        "route_enabled": route.enabled,
        "usage": {},
        "error": budget_reason,
    })
    record = AutoDebugRecord(
        experiment_id=experiment_id,
        result_id=failed_result.get("result_id", ""),
        patch_id=patch_id,
        attempt_number=attempt,
        error_summary=f"skipped: {budget_reason}",
        fix_description="",
        fix_file_contents={},
    )
    return self._persist(record, state, context, experiment_id)

# Check route enabled
if route.provider in {"offline", "local", "rule_based"}:
    self._write_llm_call_artifact(state, context.artifact_store, {
        "agent": "auto_debugger",
        "experiment_id": experiment_id,
        "result_id": failed_result.get("result_id", ""),
        "patch_id": patch_id,
        "status": "skipped_route_disabled",
        "provider": route.provider,
        "model": route.model,
        "route_enabled": route.enabled,
        "usage": {},
        "error": "",
    })
    record = AutoDebugRecord(experiment_id=experiment_id,
        result_id=failed_result.get("result_id", ""),
        patch_id=patch_id, attempt_number=attempt,
        error_summary="skipped: LLM route not enabled",
        fix_description="",
        fix_file_contents={},
    )
    return self._persist(record, state, context, experiment_id)

# No usable context
if not contexts:
    self._write_llm_call_artifact(state, context.artifact_store, {
        "agent": "auto_debugger",
        "experiment_id": experiment_id,
        "result_id": failed_result.get("result_id", ""),
        "patch_id": patch_id,
        "status": "skipped_no_context",
        "provider": route.provider,
        "model": route.model,
        "route_enabled": route.enabled,
        "usage": {},
        "error": "",
    })
    record = AutoDebugRecord(experiment_id=experiment_id,
        result_id=failed_result.get("result_id", ""),
        patch_id=patch_id, attempt_number=attempt,
        error_summary=error_text[:500] if error_text else "no error message",
        fix_description="no usable file context for LLM; manual review needed",
        fix_file_contents={},
    )
    return self._persist(record, state, context, experiment_id)

# Build prompt and call LLM
prompt = self._build_debug_prompt(experiment_id, attempt, plan, failed_result, code_patch, contexts)
response = self.llm_client.chat(route, prompt, temperature=0.1, max_tokens=3000)

call_status = "ok" if response.ok else "error"
call_data: dict = {
    "agent": "auto_debugger",
    "experiment_id": experiment_id,
    "result_id": failed_result.get("result_id", ""),
    "patch_id": patch_id,
    "status": call_status,
    "provider": route.provider,
    "model": route.model,
    "route_enabled": route.enabled,
    "usage": response.usage,
    "error": response.error if not response.ok else "",
}
self._write_llm_call_artifact(state, context.artifact_store, call_data)

if response.ok:
    record_llm_usage(state, response.usage)

# Parse and validate LLM response
fix_description = ""
fix_file_contents: dict[str, str] = {}
if response.ok:
    payload = extract_json_object(response.text)
    if payload is not None:
        fix_description = str(payload.get("fix_description", ""))
        raw_fixes = payload.get("fix_file_contents")
        if isinstance(raw_fixes, dict):
            for fpath, fcontent in raw_fixes.items():
                if not isinstance(fpath, str) or not isinstance(fcontent, str):
                    continue
                if fpath in read_only:
                    continue  # reject overwrite of read_only_context files
                if fpath not in candidates:
                    continue  # reject paths outside candidate list
                if Path(fpath).is_absolute() or ".." in Path(fpath).parts:
                    continue
                fix_file_contents[fpath] = fcontent
    else:
        self._write_llm_call_artifact(state, context.artifact_store, {
            "agent": "auto_debugger",
            "experiment_id": experiment_id,
            "result_id": failed_result.get("result_id", ""),
            "patch_id": patch_id,
            "status": "invalid_json",
            "provider": route.provider,
            "model": route.model,
            "route_enabled": route.enabled,
            "usage": {},
            "error": "JSON parse failed",
        })

record = AutoDebugRecord(
    experiment_id=experiment_id,
    result_id=failed_result.get("result_id", ""),
    patch_id=patch_id,
    attempt_number=attempt,
    error_summary=error_text[:500] if error_text else "no error message",
    fix_description=fix_description or (
        f"traceback parsed: {traceback_info}" if traceback_info
        else "no traceback found; manual review needed"
    ),
    fix_file_contents=fix_file_contents,
)
return self._persist(record, state, context, experiment_id)
```

- [ ] **Step 4: Run tests to verify pass**

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_auto_debugger -v
```

Expected: 12 tests PASS

- [ ] **Step 5: Commit**

```bash
git add agents/auto_debugger.py tests/test_auto_debugger.py
git commit -m "feat: wire LLM debug chain into AutoDebugger.run() with full audit trail"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```

---

### Task 5: ProjectSafetyPolicy integration in CodeWriter

**Files:**
- Modify: `agents/code_writer.py` (run method)
- Test: `tests/test_code_writer.py`

**Interfaces:**
- Consumes: `ProjectSafetyPolicy.from_topic()` (existing), `changes` dict, `CodePatch` (existing)
- Produces: early return with blocked status if policy violated

- [ ] **Step 1: Write failing tests**

```python
def test_policy_blocks_protected_file(self):
    with TemporaryDirectory() as tmp:
        src_dir = Path(tmp) / "src"
        src_dir.mkdir()
        (src_dir / "model").mkdir(parents=True)
        (src_dir / "model" / "secrets.py").write_text("SECRET = 'xyz'")
        (src_dir / "model" / "decoder.py").write_text("x = 1")
        state = _state()
        state.topic.codebase["repo_path"] = str(src_dir)
        state.topic.codebase["copy_can_modify"] = True  # sandbox mode
        state.topic.codebase["protected_files"] = ["model/secrets.py"]
        state.topic.codebase["allowed_auto_edit"] = ["model/"]
        state.values["experiment_plans"] = [{
            "experiment_id": "exp_1", "hypothesis": "test",
            "modification": "change secrets",
            "files_to_change": ["model/secrets.py"],
        }]
        context = AgentContext(
            artifact_store=ArtifactStore(Path(tmp) / "runs"),
            memory_store=None, tool_registry=None,
            settings={"enable_code_writes": True},
        )
        agent = CodeWriterAgent()
        result = agent.run(state, context)
        patch = state.values["code_patches_by_experiment_id"]["exp_1"]
        self.assertEqual(patch["status"], "blocked")
        self.assertIn("protected", patch["reason"])


def test_policy_blocks_max_files(self):
    with TemporaryDirectory() as tmp:
        src_dir = Path(tmp) / "src"
        src_dir.mkdir()
        (src_dir / "model").mkdir(parents=True)
        for i in range(10):
            (src_dir / "model" / f"file_{i}.py").write_text(f"# file {i}")
        state = _state()
        state.topic.codebase["repo_path"] = str(src_dir)
        state.topic.codebase["copy_can_modify"] = True
        state.topic.codebase["max_files_per_patch"] = 3
        state.topic.codebase["allowed_auto_edit"] = ["model/"]
        state.values["experiment_plans"] = [{
            "experiment_id": "exp_1", "hypothesis": "test",
            "modification": "change many files",
            "files_to_change": [f"model/file_{i}.py" for i in range(10)],
        }]
        context = AgentContext(
            artifact_store=ArtifactStore(Path(tmp) / "runs"),
            memory_store=None, tool_registry=None,
            settings={"enable_code_writes": True},
        )
        agent = CodeWriterAgent()
        result = agent.run(state, context)
        patch = state.values["code_patches_by_experiment_id"]["exp_1"]
        self.assertEqual(patch["status"], "blocked")
        self.assertIn("files", patch["reason"].lower())
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_code_writer.CodeWriterAgentTest.test_policy_blocks_protected_file tests.test_code_writer.CodeWriterAgentTest.test_policy_blocks_max_files -v
```

Expected: FAIL — expected "blocked" but got "applied" or "pending"

- [ ] **Step 3: Implement policy check in CodeWriter.run()**

In `agents/code_writer.py`, after the `if not changes:` block (line 73) and before `changed_files, backups, ok, reason = self._apply_changes(...)` (line 75), insert:

```python
        # ProjectSafetyPolicy business-rule check
        from tools.project_safety import ProjectSafetyPolicy
        policy = ProjectSafetyPolicy.from_topic(state.topic)
        problems = policy.validate_planned_paths(list(changes.keys()))
        if problems:
            patch = CodePatch(
                experiment_id=experiment_id,
                task_id=task.get("task_id", ""),
                attempt=attempt,
                mode=mode,
                work_dir=str(work_dir),
                status="blocked",
                reason="; ".join(problems),
            )
            return self._persist(patch, state, context, experiment_id)
```

- [ ] **Step 4: Run tests to verify pass**

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_code_writer -v
```

Expected: 9 tests PASS (7 existing + 2 new)

- [ ] **Step 5: Commit**

```bash
git add agents/code_writer.py tests/test_code_writer.py
git commit -m "feat: integrate ProjectSafetyPolicy into CodeWriter for topic-level path validation"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```

---

### Task 6: CodeTask experiment_id matching (fail closed)

**Files:**
- Modify: `agents/code_writer.py:48-49`
- Test: `tests/test_code_writer.py`

**Interfaces:**
- Consumes: `state.values["code_tasks"]`, `experiment_id`
- Produces: matched `task` dict or blocked CodePatch

- [ ] **Step 1: Write failing tests**

```python
def test_code_task_match_by_experiment_id(self):
    with TemporaryDirectory() as tmp:
        src_dir = Path(tmp) / "src"
        src_dir.mkdir()
        (src_dir / "model").mkdir(parents=True)
        (src_dir / "model" / "decoder.py").write_text("x = 1")
        state = _state()
        state.topic.codebase["repo_path"] = str(src_dir)
        state.topic.codebase["copy_can_modify"] = True
        state.topic.codebase["allowed_auto_edit"] = ["model/"]
        # Two code_tasks, different experiment_ids
        state.values["code_tasks"] = [
            {"task_id": "ct_a", "experiment_id": "exp_other",
             "allowed_paths": ["other/"], "protected_paths": []},
            {"task_id": "ct_b", "experiment_id": "exp_1",
             "allowed_paths": ["model/"], "protected_paths": ["model/secrets.py"]},
        ]
        state.values["experiment_plans"] = [{
            "experiment_id": "exp_1", "hypothesis": "test",
            "modification": "change decoder",
            "files_to_change": ["model/decoder.py"],
        }]
        context = AgentContext(
            artifact_store=ArtifactStore(Path(tmp) / "runs"),
            memory_store=None, tool_registry=None,
            settings={"enable_code_writes": True},
        )
        agent = CodeWriterAgent()
        result = agent.run(state, context)
        patch = state.values["code_patches_by_experiment_id"]["exp_1"]
        # Should match ct_b, not ct_a
        self.assertEqual(patch["task_id"], "ct_b")


def test_code_task_missing_blocks(self):
    with TemporaryDirectory() as tmp:
        src_dir = Path(tmp) / "src"
        src_dir.mkdir()
        (src_dir / "model").mkdir(parents=True)
        (src_dir / "model" / "decoder.py").write_text("x = 1")
        state = _state()
        state.topic.codebase["repo_path"] = str(src_dir)
        state.topic.codebase["copy_can_modify"] = True
        state.topic.codebase["allowed_auto_edit"] = ["model/"]
        # No matching code_task for exp_1
        state.values["code_tasks"] = [
            {"task_id": "ct_other", "experiment_id": "exp_other",
             "allowed_paths": ["other/"], "protected_paths": []},
        ]
        state.values["experiment_plans"] = [{
            "experiment_id": "exp_1", "hypothesis": "test",
            "modification": "change decoder",
            "files_to_change": ["model/decoder.py"],
        }]
        context = AgentContext(
            artifact_store=ArtifactStore(Path(tmp) / "runs"),
            memory_store=None, tool_registry=None,
            settings={"enable_code_writes": True},
        )
        agent = CodeWriterAgent()
        result = agent.run(state, context)
        patch = state.values["code_patches_by_experiment_id"]["exp_1"]
        self.assertEqual(patch["status"], "blocked")
        self.assertIn("no CodeTask", patch["reason"])
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_code_writer.CodeWriterAgentTest.test_code_task_match_by_experiment_id tests.test_code_writer.CodeWriterAgentTest.test_code_task_missing_blocks -v
```

Expected: FAIL — test_code_task_match_by_experiment_id fails because code_tasks[0] returns ct_a (wrong); test_code_task_missing_blocks fails because fallback {} allows apply

- [ ] **Step 3: Implement fix**

In `agents/code_writer.py`, replace lines 48-49:
```python
        code_tasks = state.values.get("code_tasks", []) or []
        task = code_tasks[0] if code_tasks else {}
```
With:
```python
        code_tasks = state.values.get("code_tasks", []) or []
        task = next(
            (
                t for t in code_tasks
                if isinstance(t, dict) and t.get("experiment_id") == experiment_id
            ),
            None,
        )
        if task is None:
            patch = CodePatch(
                experiment_id=experiment_id,
                attempt=attempt,
                mode=mode,
                work_dir=str(work_dir),
                status="blocked",
                reason=f"no CodeTask matched experiment_id={experiment_id}",
            )
            return self._persist(patch, state, context, experiment_id)
```

- [ ] **Step 4: Run tests to verify pass**

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_code_writer.CodeWriterAgentTest.test_code_task_match_by_experiment_id tests.test_code_writer.CodeWriterAgentTest.test_code_task_missing_blocks -v
```

Expected: PASS

- [ ] **Step 5: Full CodeWriter test suite**

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_code_writer -v
```

Expected: 11 tests PASS (7 existing + 4 new)

- [ ] **Step 6: Commit**

```bash
git add agents/code_writer.py tests/test_code_writer.py
git commit -m "fix: match CodeTask by experiment_id, fail closed on miss"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```

---

### Task 7: Full test suite + offline smoke + Q&A update

**Files:**
- No code changes (only verify)
- Modify: `docs/Q&A.md` (update AutoDebugger description)

- [ ] **Step 1: Run full test suite**

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest discover -s tests -p "test*.py"
```

Expected: all tests PASS (≥ 284)

- [ ] **Step 2: Run offline smoke**

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir tmp\p16_offline_smoke --max-papers 1 --enable-experiments
```

Expected: `review_status=pass`

- [ ] **Step 3: Update docs/Q&A.md**

Change the AutoDebugger pipeline description in `docs/Q&A.md`. The current description says `AutoDebuggerAgent（解析 traceback，生成修复建议，P16 LLM 路线下含实际 fix_file_contents）` — update to reflect P16 completion.

Find the relevant section and update to:
```
AutoDebuggerAgent（解析 traceback，LLM 生成 fix_file_contents，写 llm_calls artifact，P16）
```

- [ ] **Step 4: Commit Q&A update**

```bash
git add docs/Q&A.md
git commit -m "docs: update AutoDebugger description for P16 LLM chain completion"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```

---

## Task Dependency Graph

```
Task 1 (_parse_traceback fix) ─┐
Task 2 (_read_file_contexts)   ├──> Task 4 (wire LLM into run) ──> Task 7 (verify)
Task 3 (prompt + llm_calls) ──┘
Task 5 (ProjectSafetyPolicy) ──────────────────────────────────────> Task 7
Task 6 (CodeTask matching) ────────────────────────────────────────> Task 7
```

Tasks 1-3 can be done in parallel. Tasks 5-6 can be done in parallel. Task 4 depends on 1-3. Task 7 is the final gate.
