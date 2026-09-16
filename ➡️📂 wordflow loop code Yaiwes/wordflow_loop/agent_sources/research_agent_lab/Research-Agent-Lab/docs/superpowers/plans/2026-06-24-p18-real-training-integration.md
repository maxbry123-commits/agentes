# P18: Real Training Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the system execute actual training/evaluation on Intent-LED-mul-agent with per-experiment command overrides and human-controllable budget limits.

**Architecture:** Add `commands` field to ExperimentPlan schema; add `_resolve_commands` + `_apply_budget` to AutonomousExperimentAgent; add `experiment_tag` to topic pack; wire `--train-budget-epochs/--train-budget-minutes` CLI flags through factory to agent context. No new agent, no schema breaking.

**Tech Stack:** Python 3.11, dataclasses, argparse, subprocess, re. Existing test patterns: `from x import y` directly, no pytest.

**Test runner:** `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest discover -s tests -p "test*.py"`

## Global Constraints

- `ExperimentPlan.commands` default `[]` means "use codebase_report.smoke_commands" (full backward compatibility)
- `train_budget_epochs` and `train_budget_minutes` default `None` means no budget enforcement
- All budget enforcement only reduces existing limits, never extends them
- `--max_epochs` is the real script flag, NOT `--epochs`
- `experiment_tag` defaults to `"motion_condition"` when absent from topic pack
- No changes to ExperimentOrchestratorAgent, CodeWriterAgent, AutoDebuggerAgent, ExperimentResult, ScopedCodeExecutor, _normalize_command, _rewrite_python, _CD_PATTERN

---

### Task 1: Schema — ExperimentPlan.commands + topic experiment_tag

**Files:**
- Modify: `schemas/experiment_plan.py:22` (add `commands` field)
- Modify: `topics/intent_led_virat.json:58` (add `experiment_tag`)

**Interfaces:**
- Produces: `ExperimentPlan.commands: list[str]` (default `[]`), read by Task 3 via `plan.get("commands", [])`
- Produces: `topic.codebase["experiment_tag"]` (default `"motion_condition"`), read by Task 2 via `topic.codebase.get("experiment_tag", "motion_condition")`

- [ ] **Step 1: Add `commands` field to ExperimentPlan**

In `schemas/experiment_plan.py`, after the `rollback_plan` field (line 22), add:

```python
commands: list[str] = field(default_factory=list)
```

- [ ] **Step 2: Add `experiment_tag` to topic pack**

In `topics/intent_led_virat.json`, inside the `"codebase"` object (before `"repo_path"` on line 57), add:

```json
"experiment_tag": "intention_baseline",
```

- [ ] **Step 3: Run existing tests to verify no regression**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest discover -s tests -p "test*.py" -q`
Expected: 316 tests pass, OK

- [ ] **Step 4: Commit**

```bash
git add schemas/experiment_plan.py topics/intent_led_virat.json
git commit -m "feat: add ExperimentPlan.commands and topic codebase.experiment_tag for P18"
```

---

### Task 2: CodebaseAnalyzer — unhardcode experiment_tag

**Files:**
- Modify: `tools/codebase_analyzer.py:136`
- Test: `tests/test_codebase_analyzer.py` (add 2 tests)

**Interfaces:**
- Consumes: `topic.codebase.get("experiment_tag", "motion_condition")` from Task 1
- Produces: smoke commands with dynamic `--info` flag (same interface as before)

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_codebase_analyzer.py` after the existing `CodebaseAnalyzerTest` class:

```python
class CodebaseAnalyzerExperimentTagTest(unittest.TestCase):
    def test_experiment_tag_from_topic_pack(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "work.md").write_text("# test", encoding="utf-8")
            topic = TopicPack.from_mapping({
                "topic_name": "test",
                "codebase": {
                    "repo_path": str(root),
                    "experiment_tag": "custom_tag",
                    "allowed_auto_edit": [],
                },
            })
            report = CodebaseAnalyzer().analyze(topic)
            self.assertEqual(len(report.smoke_commands), 2)
            self.assertIn("--info custom_tag", report.smoke_commands[0])
            self.assertIn("--info custom_tag", report.smoke_commands[1])

    def test_experiment_tag_default_when_absent(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "work.md").write_text("# test", encoding="utf-8")
            topic = TopicPack.from_mapping({
                "topic_name": "test",
                "codebase": {
                    "repo_path": str(root),
                    "allowed_auto_edit": [],
                },
            })
            report = CodebaseAnalyzer().analyze(topic)
            self.assertIn("--info motion_condition", report.smoke_commands[0])
```

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_codebase_analyzer.CodebaseAnalyzerExperimentTagTest -v`
Expected: 2 tests — `test_experiment_tag_from_topic_pack` FAIL, `test_experiment_tag_default_when_absent` PASS (both conditions match current hardcoded "motion_condition" behavior).

- [ ] **Step 2: Run test to verify one fails**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_codebase_analyzer.CodebaseAnalyzerExperimentTagTest.test_experiment_tag_from_topic_pack -v`
Expected: FAIL — `'--info custom_tag' not found in 'cd /d ... --info motion_condition'`

- [ ] **Step 3: Implement the change**

In `tools/codebase_analyzer.py`, change line 136 from:

```python
        info = "motion_condition"
```

To:

```python
        info = topic.codebase.get("experiment_tag", "motion_condition")
```

- [ ] **Step 4: Run tests to verify pass**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_codebase_analyzer -v`
Expected: 3 tests pass (existing + 2 new)

- [ ] **Step 5: Commit**

```bash
git add tools/codebase_analyzer.py tests/test_codebase_analyzer.py
git commit -m "feat: read codebase.experiment_tag from topic pack instead of hardcoded motion_condition"
```

---

### Task 3: AutonomousExperimentAgent — command resolution + budget enforcement

**Files:**
- Modify: `agents/autonomous_experiment.py:86-91,100-105,107-114,120` (replace `_smoke_commands`, add `_resolve_commands` + `_apply_budget`, modify `_execute_and_parse` signature)
- Test: `tests/test_autonomous_experiment.py` (add 10 tests)

**Interfaces:**
- Consumes: `plan.get("commands", [])` from Task 1 schema, `context.settings.get("train_budget_epochs")` and `context.settings.get("train_budget_minutes")` from Task 5
- Produces: `_resolve_commands(state, plan) -> list[str]`, `_apply_budget(commands, settings) -> list[str]`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_autonomous_experiment.py` after the existing `NormalizeCommandTest` class:

```python
class ResolveCommandsTest(TestCase):
    def test_uses_plan_commands_when_present(self):
        agent = AutonomousExperimentAgent()
        state = _make_state("/fake", [])
        plan = {"commands": ["python -c \"print('plan_cmd')\""]}
        result = agent._resolve_commands(state, plan)
        self.assertEqual(len(result), 1)
        self.assertIn("plan_cmd", result[0])

    def test_falls_back_to_smoke_when_plan_commands_empty(self):
        agent = AutonomousExperimentAgent()
        state = _make_state("/fake", ["python -c \"print('smoke_cmd')\""])
        plan = {"commands": []}
        result = agent._resolve_commands(state, plan)
        self.assertEqual(len(result), 1)
        self.assertIn("smoke_cmd", result[0])

    def test_falls_back_to_smoke_when_plan_commands_missing(self):
        agent = AutonomousExperimentAgent()
        state = _make_state("/fake", ["python -c \"print('smoke_cmd')\""])
        plan = {}
        result = agent._resolve_commands(state, plan)
        self.assertEqual(len(result), 1)
        self.assertIn("smoke_cmd", result[0])

    def test_noop_fallback_when_both_empty(self):
        agent = AutonomousExperimentAgent()
        state = _make_state("/fake", [])
        plan = {}
        result = agent._resolve_commands(state, plan)
        self.assertEqual(len(result), 1)
        self.assertIn("no smoke commands configured", result[0])


class ApplyBudgetTest(TestCase):
    def test_appends_max_epochs_when_missing(self):
        agent = AutonomousExperimentAgent()
        cmds = ["python train.py --train 1"]
        result = agent._apply_budget(cmds, {"train_budget_epochs": 5})
        self.assertIn("--max_epochs 5", result[0])

    def test_replaces_max_epochs_when_present(self):
        agent = AutonomousExperimentAgent()
        cmds = ["python train.py --max_epochs 100 --train 1"]
        result = agent._apply_budget(cmds, {"train_budget_epochs": 5})
        self.assertIn("--max_epochs 5", result[0])
        self.assertNotIn("100", result[0])

    def test_noop_when_budget_none(self):
        agent = AutonomousExperimentAgent()
        cmds = ["python train.py --train 1"]
        result = agent._apply_budget(cmds, {"train_budget_epochs": None})
        self.assertEqual(result, cmds)

    def test_noop_when_budget_missing(self):
        agent = AutonomousExperimentAgent()
        cmds = ["python train.py --train 1"]
        result = agent._apply_budget(cmds, {})
        self.assertEqual(result, cmds)

    def test_handles_multiple_commands(self):
        agent = AutonomousExperimentAgent()
        cmds = [
            "python train.py --train 1",
            "python train.py --max_epochs 50 --train 0",
        ]
        result = agent._apply_budget(cmds, {"train_budget_epochs": 3})
        self.assertIn("--max_epochs 3", result[0])
        self.assertIn("--max_epochs 3", result[1])


class ExecuteAndParseBudgetTest(TestCase):
    def test_respects_budget_timeout_when_set(self):
        with TemporaryDirectory() as tmp:
            work = Path(tmp) / "repo"
            work.mkdir()
            agent = AutonomousExperimentAgent()
            state = _make_state(str(work), [])
            result = agent._execute_and_parse(
                experiment_id="test",
                command="python -c \"print('ADE: 0.3')\"",
                work_dir=str(work),
                state=state,
                success_criteria=None,
                settings={"train_budget_minutes": 5},
            )
            self.assertEqual(result.status, "passed")
```

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_autonomous_experiment.ResolveCommandsTest tests.test_autonomous_experiment.ApplyBudgetTest tests.test_autonomous_experiment.ExecuteAndParseBudgetTest -v`
Expected: ALL FAIL — `_resolve_commands`, `_apply_budget` don't exist yet, `_execute_and_parse` doesn't accept `settings`.

- [ ] **Step 2: Verify tests fail**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_autonomous_experiment.ResolveCommandsTest.test_uses_plan_commands_when_present -v`
Expected: FAIL with `AttributeError: 'AutonomousExperimentAgent' object has no attribute '_resolve_commands'`

- [ ] **Step 3: Replace `_smoke_commands` with `_resolve_commands`**

In `agents/autonomous_experiment.py`, replace the existing `_smoke_commands` method (lines 100-105):

```python
    def _resolve_commands(self, state: ResearchState, plan: dict) -> list[str]:
        plan_commands = plan.get("commands", []) or []
        if plan_commands:
            return [_rewrite_python(cmd) for cmd in plan_commands]

        report = state.values.get("codebase_report", {})
        commands = report.get("smoke_commands", [])
        if not commands:
            commands = ["python -c \"print('no smoke commands configured; nothing to run')\""]
        return [_rewrite_python(cmd) for cmd in commands]
```

- [ ] **Step 4: Add `_apply_budget` method**

Add after `_resolve_commands` in `agents/autonomous_experiment.py`:

```python
    def _apply_budget(self, commands: list[str], settings: dict) -> list[str]:
        epochs = settings.get("train_budget_epochs")
        if not epochs:
            return commands
        result = []
        for cmd in commands:
            if "--max_epochs" in cmd:
                cmd = re.sub(r"--max_epochs\s+\d+", f"--max_epochs {epochs}", cmd)
            else:
                cmd += f" --max_epochs {epochs}"
            result.append(cmd)
        return result
```

- [ ] **Step 5: Update `run_single_plan` call site**

In `agents/autonomous_experiment.py`, change lines 87-96:

Replace:
```python
        smoke_commands = self._smoke_commands(state)
        results: list[dict] = []
        for cmd in smoke_commands:
            result = self._execute_and_parse(experiment_id, cmd, work_dir, state, success_criteria)
```

With:
```python
        commands = self._resolve_commands(state, plan)
        commands = self._apply_budget(commands, context.settings)
        results: list[dict] = []
        for cmd in commands:
            result = self._execute_and_parse(experiment_id, cmd, work_dir, state, success_criteria, context.settings)
```

- [ ] **Step 6: Add `settings` parameter to `_execute_and_parse`**

Change the signature from (line 107-113):
```python
    def _execute_and_parse(
        self,
        experiment_id: str,
        command: str,
        work_dir: str,
        state: ResearchState,
        success_criteria: dict | None = None,
    ) -> ExperimentResult:
```

To:
```python
    def _execute_and_parse(
        self,
        experiment_id: str,
        command: str,
        work_dir: str,
        state: ResearchState,
        success_criteria: dict | None = None,
        settings: dict | None = None,
    ) -> ExperimentResult:
```

And change line 120 from:
```python
            completed = executor.run(cmd_parts, cwd=cwd, timeout=_SMOKE_TIMEOUT)
```

To:
```python
            timeout = _SMOKE_TIMEOUT
            if settings and settings.get("train_budget_minutes"):
                timeout = min(_SMOKE_TIMEOUT, int(settings["train_budget_minutes"]) * 60)
            completed = executor.run(cmd_parts, cwd=cwd, timeout=timeout)
```

- [ ] **Step 7: Run all autonomous_experiment tests**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_autonomous_experiment -v`
Expected: 24 tests pass (14 existing + 10 new)

- [ ] **Step 8: Run full test suite to verify no regression**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest discover -s tests -p "test*.py" -q`
Expected: ≥ 328 tests pass, OK (316 base + 2 from Task 2 + 10 from Task 3, Tasks 4 and 5 not yet merged)

- [ ] **Step 9: Commit**

```bash
git add agents/autonomous_experiment.py tests/test_autonomous_experiment.py
git commit -m "feat: add _resolve_commands, _apply_budget, and budget timeout to AutonomousExperimentAgent"
```

---

### Task 4: ExperimentPlannerAgent — LLM path commands extraction

**Files:**
- Modify: `agents/experiment_planner.py:177-189,203,226-241` (add `commands` to `fields`, fix LLM prompt, extract in `_plan_from_payload`)
- Test: `tests/test_synthesis_and_planner_llm.py` (add 2 tests)

**Interfaces:**
- Consumes: `ExperimentPlan.commands` from Task 1 schema
- Produces: ExperimentPlan with `commands` field populated from LLM response (or empty list from rule-based path)

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_synthesis_and_planner_llm.py` after the existing `SynthesisAndPlannerLLMTest` class:

```python
class ExperimentPlannerCommandsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.old_key = os.environ.get("DEEPSEEK_API_KEY")
        os.environ["DEEPSEEK_API_KEY"] = "sk-test-key-for-route-enable"

    def tearDown(self) -> None:
        if self.old_key is None:
            os.environ.pop("DEEPSEEK_API_KEY", None)
        else:
            os.environ["DEEPSEEK_API_KEY"] = self.old_key

    def test_plan_from_payload_extracts_commands(self):
        agent = ExperimentPlannerAgent()
        state = ResearchState(topic=make_topic())
        state.values["opportunities"] = [{"title": "test", "hypothesis": "test", "technical_strategy": "test"}]
        state.values["codebase_report"] = {"suggested_first_patch_files": []}
        base_plan = agent._rule_based_plan(state)
        payload = {
            "name": "test",
            "hypothesis": "test",
            "files_to_change": [],
            "commands": ["python train.py --train 1 --max_epochs 10"],
        }
        plan = agent._plan_from_payload(state, payload, base_plan)
        self.assertEqual(plan.commands, ["python train.py --train 1 --max_epochs 10"])

    def test_plan_from_payload_commands_default_to_empty(self):
        agent = ExperimentPlannerAgent()
        state = ResearchState(topic=make_topic())
        state.values["opportunities"] = [{"title": "test", "hypothesis": "test", "technical_strategy": "test"}]
        state.values["codebase_report"] = {"suggested_first_patch_files": []}
        base_plan = agent._rule_based_plan(state)
        payload = {"name": "test", "hypothesis": "test", "files_to_change": []}
        plan = agent._plan_from_payload(state, payload, base_plan)
        self.assertEqual(plan.commands, [])
```

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_synthesis_and_planner_llm.ExperimentPlannerCommandsTest -v`
Expected: 2 tests FAIL — `_plan_from_payload` doesn't extract `commands` yet.

- [ ] **Step 2: Verify tests fail**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_synthesis_and_planner_llm.ExperimentPlannerCommandsTest.test_plan_from_payload_extracts_commands -v`
Expected: FAIL — `AssertionError: [] != ['python train.py --train 1 --max_epochs 10']`

- [ ] **Step 3: Add `commands` to `fields` list**

In `agents/experiment_planner.py`, line 177-189, add `"commands"` at the end of the `fields` list:

```python
        fields = [
            "name",
            "hypothesis",
            "baseline",
            "modification",
            "files_to_change",
            "dataset",
            "training_config",
            "metrics",
            "ablation_studies",
            "acceptance_criteria",
            "rollback_plan",
            "commands",
        ]
```

- [ ] **Step 4: Add `commands` to `_plan_from_payload` constructor**

In `agents/experiment_planner.py`, in the `ExperimentPlan(...)` constructor call (after `rollback_plan` line 241), add:

```python
            commands=self._as_str_list(payload.get("commands"), base_plan.commands),
```

- [ ] **Step 5: Fix LLM prompt text**

In `agents/experiment_planner.py`, change line 203 from:

```python
                    "The plan must include concrete files_to_change, smoke-test commands inside training_config, "
```

To:

```python
                    "The plan must include concrete files_to_change, commands (list of shell command strings like "
                    "['python main.py --train 1 --max_epochs 5']), "
```

- [ ] **Step 6: Run experiment_planner tests**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_synthesis_and_planner_llm.ExperimentPlannerCommandsTest -v`
Expected: 2 tests pass

- [ ] **Step 7: Run full test suite**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest discover -s tests -p "test*.py" -q`
Expected: ≥ 330 tests pass, OK (316 base + 2 from Task 2 + 10 from Task 3 + 2 from Task 4, Task 5 not yet merged)

- [ ] **Step 8: Commit**

```bash
git add agents/experiment_planner.py tests/test_synthesis_and_planner_llm.py
git commit -m "feat: extract commands from LLM response in ExperimentPlannerAgent"
```

---

### Task 5: CLI and Workflow Integration

**Files:**
- Modify: `app/main.py:117,235-255` (add 2 CLI args, pass through to factory)
- Modify: `workflows/factory.py:37-57,103-120` (add 2 params, 2 settings keys)
- Test: `tests/test_full_research_loop.py` (add 2 tests to `CliParserTest`)

**Interfaces:**
- Consumes: None from earlier tasks (independent integration layer)
- Produces: `context.settings["train_budget_epochs"]` and `context.settings["train_budget_minutes"]` consumed by Task 3

- [ ] **Step 1: Write the failing tests**

In `tests/test_full_research_loop.py`, add to the `CliParserTest` class (after `test_reference_expansion_flags_parse`):

```python
    def test_train_budget_epochs_flag_parses(self):
        from app.main import build_parser

        parser = build_parser()
        args = parser.parse_args([
            "run",
            "--topic", "topics/intent_led_virat.json",
            "--train-budget-epochs", "5",
        ])

        self.assertEqual(args.train_budget_epochs, 5)

    def test_train_budget_minutes_flag_parses(self):
        from app.main import build_parser

        parser = build_parser()
        args = parser.parse_args([
            "run",
            "--topic", "topics/intent_led_virat.json",
            "--train-budget-minutes", "30",
        ])

        self.assertEqual(args.train_budget_minutes, 30)
```

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_full_research_loop.CliParserTest.test_train_budget_epochs_flag_parses -v`
Expected: FAIL — unrecognized arguments.

- [ ] **Step 2: Add CLI args to `build_parser()`**

In `app/main.py`, after line 117 (after `--retrieval-judge-top-k`), add:

```python
    run_parser.add_argument(
        "--train-budget-epochs",
        type=int,
        default=None,
        help="Max training epochs per experiment",
    )
    run_parser.add_argument(
        "--train-budget-minutes",
        type=int,
        default=None,
        help="Max training minutes per experiment command",
    )
```

- [ ] **Step 3: Pass new args through `run_workflow()`**

In `app/main.py`, in the `build_full_research_workflow()` call (after line 254), add:

```python
        train_budget_epochs=args.train_budget_epochs,
        train_budget_minutes=args.train_budget_minutes,
```

- [ ] **Step 4: Add params to factory**

In `workflows/factory.py`:

Add two parameters to the function signature (after line 56):

```python
    train_budget_epochs: int | None = None,
    train_budget_minutes: int | None = None,
```

Add two keys to the `settings` dict (after line 119):

```python
            "train_budget_epochs": train_budget_epochs,
            "train_budget_minutes": train_budget_minutes,
```

- [ ] **Step 5: Run CLI tests**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest tests.test_full_research_loop.CliParserTest -v`
Expected: 3 tests pass (existing + 2 new)

- [ ] **Step 6: Run full test suite**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest discover -s tests -p "test*.py" -q`
Expected: 332 tests pass (316 base + 16 new across all tasks)

- [ ] **Step 7: Commit**

```bash
git add app/main.py workflows/factory.py tests/test_full_research_loop.py
git commit -m "feat: add --train-budget-epochs and --train-budget-minutes CLI flags"
```

---

### Task 6: Full Verification

**Files:**
- No code changes (verification only)

- [ ] **Step 1: Run full test suite**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m unittest discover -s tests -p "test*.py" -q`
Expected: 332 tests pass, OK

- [ ] **Step 2: Run offline smoke test**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m app.main run --topic topics/intent_led_virat.json --data-dir data --max-papers 1`
Expected: `run_id=...`, `stage=completed`, `review_status=pass`

- [ ] **Step 3: Verify budget flags parse**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -m app.main run --help 2>&1 | findstr train-budget`
Expected: both `--train-budget-epochs` and `--train-budget-minutes` appear in help output

- [ ] **Step 4: Verify smoke commands use experiment_tag**

Run: `D:/Develop_Tools/Anaconda3/envs/video_llava/python.exe -c "from tools.codebase_analyzer import CodebaseAnalyzer; from schemas.topic_pack import TopicPack; import json; t = TopicPack.from_mapping(json.load(open('topics/intent_led_virat.json'))); r = CodebaseAnalyzer().analyze(t); print(r.smoke_commands[0])"`
Expected: output contains `--info intention_baseline` (NOT `motion_condition`)

- [ ] **Step 5: Commit verification results**

```bash
git add -A
git diff --cached --stat
```

If all clean: done. If stray files: commit only relevant ones.
