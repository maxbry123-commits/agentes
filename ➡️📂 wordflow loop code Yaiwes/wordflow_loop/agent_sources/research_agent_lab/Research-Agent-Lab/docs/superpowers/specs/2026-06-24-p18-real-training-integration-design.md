# P18: Real Training Integration Design

## Goal

Make the system execute actual training/evaluation on the Intent-LED-mul-agent codebase with per-experiment command overrides and human-controllable budget limits, instead of running only hardcoded smoke commands.

## Architecture

Three insertion points, no new agent:

```
CodebaseAnalyzer → ... → ExperimentPlannerAgent → DeveloperAgent → ExperimentOrchestratorAgent → AutonomousExperimentAgent
                              ↑ 新增 commands 字段                            ↑ 传递 context.settings    ↑ _resolve_commands + _apply_budget
```

| # | Change | File | Breaking |
|---|--------|------|----------|
| 1 | `commands` field + topic `experiment_tag` | `schemas/experiment_plan.py`, `topics/*.json` | No |
| 2 | Command resolution + budget enforcement | `agents/autonomous_experiment.py` | No |
| 3 | CLI flags + settings plumbing | `app/main.py`, `workflows/factory.py` | No |
| 4 | LLM path commands extraction | `agents/experiment_planner.py` | No |
| 5 | Unhardcode experiment tag | `tools/codebase_analyzer.py` | No |

---

## Section 1: Schema Changes

### ExperimentPlan.commands

File: `schemas/experiment_plan.py`

Add one field to the existing dataclass:

```python
commands: list[str] = field(default_factory=list)
```

Semantics: empty list = use `codebase_report.smoke_commands` (existing behavior). Non-empty = run these exact commands instead.

Zero existing code references `plan.commands`. `asdict()` serializes it automatically. `ExperimentResult` already has a `commands: list[str]` field (line 23) that is currently unused — it will be populated from the plan.

### Topic pack experiment_tag

File: `topics/intent_led_virat.json` (and future topic packs)

Optional field under `codebase`:

```json
{
  "codebase": {
    "experiment_tag": "intention_baseline"
  }
}
```

Default: `"motion_condition"` (current hardcoded value). This determines the `--info` flag passed to `main_led_nba.py`.

---

## Section 2: Command Resolution Chain

File: `agents/autonomous_experiment.py`

### `_resolve_commands(state, plan)` — replaces `_smoke_commands(state)`

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

Priority: plan.commands > codebase_report.smoke_commands > no-op fallback.

### `_apply_budget(commands, settings)` — appends/overrides `--max_epochs`

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

Uses `--max_epochs` because the target script `main_led_nba.py` defines `--max_epochs` (default 128), not `--epochs`.

### `run_single_plan()` call site

```python
def run_single_plan(self, state, context, plan, patch_dict=None, attempt=0):
    ...
    commands = self._resolve_commands(state, plan)
    commands = self._apply_budget(commands, context.settings)
    for cmd in commands:
        result = self._execute_and_parse(experiment_id, cmd, work_dir, state,
                                         success_criteria, context.settings)
```

### `_execute_and_parse()` — timeout budget

Add `settings=None` parameter at end (backward compatible):

```python
def _execute_and_parse(self, experiment_id, command, work_dir, state,
                       success_criteria=None, settings=None):
    ...
    timeout = _SMOKE_TIMEOUT
    if settings and settings.get("train_budget_minutes"):
        timeout = min(_SMOKE_TIMEOUT, int(settings["train_budget_minutes"]) * 60)
    completed = executor.run(cmd_parts, cwd=cwd, timeout=timeout)
```

Budget only reduces timeout, never extends beyond `_SMOKE_TIMEOUT` (600s default).

---

## Section 3: LLM Path

File: `agents/experiment_planner.py`

### Add `commands` to fields list

Line 177-189: add `"commands"` to the `fields` list so the LLM knows to generate it:

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
    "commands",  # 新增
]
```

### `_plan_from_payload()` — extract commands

Add to `ExperimentPlan(...)` constructor call:

```python
commands=self._as_str_list(payload.get("commands"), base_plan.commands),
```

`_as_str_list(None, [])` returns `[]`, which triggers fallback to smoke commands.

### LLM prompt fix

Change line 203 from:

```
"smoke-test commands inside training_config, "
```

To:

```
"commands (list of shell command strings like "
"['python main.py --train 1 --max_epochs 5']), "
```

The LLM already receives `base_plan` with `commands: []` in the payload, so it sees the expected shape.

---

## Section 4: CodebaseAnalyzer

File: `tools/codebase_analyzer.py`

Change line 136 from:

```python
info = "motion_condition"
```

To:

```python
info = topic.codebase.get("experiment_tag", "motion_condition")
```

All codebase accesses use `.get()` with defaults — consistent with existing pattern.

---

## Section 5: CLI and Workflow Integration

### New CLI flags

File: `app/main.py` — appended to `run` subparser (after `--retrieval-judge-top-k`):

```python
run_parser.add_argument("--train-budget-epochs", type=int, default=None,
    help="Max training epochs per experiment")
run_parser.add_argument("--train-budget-minutes", type=int, default=None,
    help="Max training minutes per experiment command")
```

### Factory

File: `workflows/factory.py`

Two new parameters (`train_budget_epochs: int | None = None`, `train_budget_minutes: int | None = None`), passed through to `settings` dict. Persisted via `_public_workflow_settings()` (not sensitive — suffix check allows them through).

### run_workflow passthrough

File: `app/main.py:235-255` — two new kwargs in `build_full_research_workflow()` call.

---

## Section 6: Testing Strategy

| Test | File | Coverage |
|------|------|----------|
| `test_resolve_commands_uses_plan_first` | `test_autonomous_experiment.py` | plan.commands takes priority |
| `test_resolve_commands_falls_back_to_smoke` | `test_autonomous_experiment.py` | empty commands → smoke |
| `test_resolve_commands_noop_fallback` | `test_autonomous_experiment.py` | both empty → noop message |
| `test_apply_budget_appends_max_epochs` | `test_autonomous_experiment.py` | append when missing |
| `test_apply_budget_replaces_max_epochs` | `test_autonomous_experiment.py` | replace when present |
| `test_apply_budget_noop_when_none` | `test_autonomous_experiment.py` | None budget = no change |
| `test_apply_budget_handles_multiple_commands` | `test_autonomous_experiment.py` | batch command processing |
| `test_execute_and_parse_respects_budget_timeout` | `test_autonomous_experiment.py` | timeout from settings |
| `test_experiment_tag_from_topic_pack` | `test_codebase_analyzer.py` | reads experiment_tag |
| `test_experiment_tag_default` | `test_codebase_analyzer.py` | fallback "motion_condition" |
| `test_plan_from_payload_extracts_commands` | `test_synthesis_and_planner_llm.py` | LLM commands extraction |
| `test_plan_from_payload_commands_default` | `test_synthesis_and_planner_llm.py` | fallback to [] |
| `test_cli_train_budget_epochs` | `test_full_research_loop.py` | --train-budget-epochs parsed |
| `test_cli_train_budget_minutes` | `test_full_research_loop.py` | --train-budget-minutes parsed |

Expected: ≥ 332 tests pass (316 existing + 16 new).

## What Is Not Changed

- No new agent
- No changes to `ExperimentOrchestratorAgent`, `CodeWriterAgent`, `AutoDebuggerAgent`
- No changes to `ExperimentResult` schema (already has `commands` field)
- No changes to `ScopedCodeExecutor`
- No changes to `_normalize_command` / `_rewrite_python` / `_CD_PATTERN`
- No sub-section detection
- No GROBID/Docling integration
