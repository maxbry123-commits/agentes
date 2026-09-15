# P17: Run Validation And Delivery Hardening Design

## Purpose

P8-P16 have made the system capable of literature retrieval, memory reuse, experiment tree management, controlled experiment execution, and LLM-assisted auto-debugging. The next risk is no longer a missing agent. The risk is that a run can appear successful while its artifacts, cross-links, documentation, or reproducibility evidence are incomplete.

P17 adds a final validation layer and a dynamic verification matrix. The goal is to make every important run inspectable by another developer without reconstructing context from terminal output.

## Scope

P17 includes:

- A schema-backed run artifact validation report.
- A validator tool that checks completed run directories and in-progress workflow state.
- A workflow agent that writes a `run_validations` artifact near the end of every run.
- A `validate-run` CLI command for validating an existing run directory after completion.
- A documented dynamic validation matrix for offline, retrieval, experiment, LLM-budget, and required real-API smoke runs.
- Updates to `docs/project_handoff.md` and `docs/Q&A.md` so the handoff reflects P15 and P16.

P17 does not include:

- New research strategy search.
- New LLM routes.
- New automatic code-writing behavior.
- New vector database or long-term storage dependency.
- Network calls in unit tests.

## Current Baseline

Current verified baseline before P17:

- Full tests: `Ran 297 tests ... OK`.
- P16 focused tests: `Ran 37 tests ... OK`.
- P16 dynamic checks:
  - task-level `allowed_paths` can narrow topic-level scope.
  - task-level `protected_paths` can block protected writes.
  - glob paths such as `models/*` still work.
  - invalid JSON LLM responses produce one `invalid_json` artifact and populate `llm_call_id`.

Current delivery gaps:

- `docs/project_handoff.md` is stale and still says P14 is the latest completed phase.
- `tmp/p16_offline_smoke/`, `tmp_dynamic_audit.py`, and `.superpowers/.../state` are untracked local artifacts that must be classified before handoff. They must not be deleted automatically.
- There is no one-command validator for an existing run directory.
- `RunEvaluationAgent` checks scientific and workflow quality, but it does not fully verify artifact index integrity, required file presence, or cross-artifact links.

## Design Approach

Recommended approach: add a lightweight validation layer instead of overloading `RunEvaluationAgent`.

Alternative A would extend `RunEvaluationAgent` directly. That would be smaller, but it would mix scientific quality scoring with filesystem and artifact integrity checks.

Alternative B would only add documentation and manual commands. That would avoid code changes, but it would not prevent broken artifact links from silently passing future runs.

P17 uses a dedicated schema, validator tool, workflow agent, and CLI. This keeps validation deterministic and easy to test while leaving existing research decisions untouched.

## Components

### 1. `schemas/run_validation.py`

Defines:

- `RunValidationCheck`
- `RunValidationReport`

The schema mirrors the style of `schemas/run_evaluation.py` but focuses on reproducibility and artifact integrity rather than research quality.

Required fields:

- `validation_id`
- `status`: `pass`, `needs_review`, or `block`
- `score`
- `run_id`
- `run_dir`
- `checks`
- `blocking_issues`
- `warnings`
- `summary`

### 2. `tools/run_artifact_validator.py`

Responsibilities:

- Read `state.json`.
- Read public workflow settings from `state.values["workflow_settings"]` when present.
- Read `artifact_index.jsonl`.
- Check index rows are valid JSON.
- Check indexed paths exist.
- Check state-declared artifacts exist on disk.
- Check required artifact kinds based on run settings and observed state.
- Check cross-links:
  - `AutoDebugRecord.llm_call_id` must resolve to `artifacts/llm_calls/<id>.json` when present.
  - `ExperimentResult.patch_id` must resolve to a known `CodePatch.patch_id` when present.
  - `CodePatch.experiment_id` must match an experiment plan id when plans exist.
  - `ExperimentDecision.experiment_id` must match an experiment result or plan id when present.
  - Cross-link id sources must merge artifact files and `state.values` fallback, because branch-derived plans can be stored in `state.values["experiment_plans"]` while their separate artifact kind is `branch_experiment_plans`.
- Check secret leakage in JSON/text artifacts using conservative patterns:
  - `sk-` tokens longer than 12 chars are a blocker.
  - strings containing `DEEPSEEK_API_KEY=` followed by a non-empty value are a blocker.
- Return a `RunValidationReport` dict or dataclass.

Severity rules:

- Missing `state.json`: blocker.
- Invalid `state.json`: blocker.
- Missing `artifact_index.jsonl`: warning unless no artifacts exist.
- Indexed file missing: blocker.
- State artifact missing: blocker.
- Cross-link missing: blocker.
- Optional artifact absent when the corresponding feature is disabled: info.
- LLM artifacts absent when `enable_llm` is false: info.
- LLM artifacts absent when `enable_llm` is true: warning, because some LLM-enabled runs can still avoid calls through route or budget gating.
- Secret leak: blocker.
- Public workflow setting persistence must preserve non-secret budget fields such as `llm_token_budget` and `llm_tokens_used`. Sensitive filtering should match API keys, secrets, and actual token credential keys, not every key containing the substring `token`.

### 3. `agents/run_validation_agent.py`

Runs after `RunEvaluationAgent` and before `LiteratureMemoryPersistenceAgent`.

It validates the current run directory with `expect_completed=False`, because `Workflow.run()` sets `state.stage = "completed"` only after all agents finish.
It passes `context.settings` into the validator, so in-progress validation does not depend only on persisted state.

It writes:

- `artifacts/run_validations/<validation_id>.json`
- `state.values["run_validation"]`
- `state.values["run_validation_status"]`
- `state.values["run_validation_score"]`

It does not block the workflow directly. Blocking is expressed in the report and can be enforced by external automation later.

### 4. `app.main validate-run`

Adds a CLI command:

```bash
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main validate-run --run-dir data\runs\<run_id>
```

Options:

- `--run-dir`: required path to a run directory.
- `--json`: print full validation JSON.
- `--strict`: return exit code 1 when status is `block`; without strict, print the report and return 0 for inspection.

The CLI validates with `expect_completed=True`.

### 5. Dynamic Validation Matrix

P17 defines a small set of dynamic validation commands. They are not unit tests; they are smoke checks that create real run directories and then validate them.

Matrix:

1. Offline minimal run
   - No LLM.
   - No experiments.
   - Expected: workflow completes, run validation status is `pass` or `needs_review`, no secret leak.

2. Retrieval evaluation run
   - `--enable-retrieval-evaluation`.
   - Expected: `retrieval_evaluations` artifact exists and run validation links it from state.

3. LLM budget-zero run
   - `--enable-llm --llm-call-budget 0`.
   - Expected: no real API usage, skipped LLM records are valid when produced, validation does not require successful LLM output.

4. Experiment smoke run
   - `--enable-experiments`.
   - Expected: `experiment_results`, `code_patches`, and `run_evaluations` exist and cross-link.
   - Does not require `--enable-code-writes`.

5. Real API smoke run
   - `--enable-llm --llm-call-budget 2 --llm-token-budget 12000`.
   - Expected: real LLM calls are recorded under `llm_calls`, validator cross-links them, and no secret material is written to artifacts.
   - This is required by the user, but must stay budget-capped.

6. Optional debug-loop run
   - `--enable-experiments --enable-code-writes --enable-llm`.
   - Must use tiny budgets and copy-mode target code.
   - Expected: if auto-debug triggers, `auto_debug_records` link to `llm_calls`.
   - This remains optional because it can modify the copied target repo.

### 6. Documentation Updates

`docs/project_handoff.md` must be brought current to P17:

- Update timestamp to `2026-06-24（P17 规划/实施中）` during implementation.
- Add P15 ExperimentOrchestrator, CodeWriter, AutoDebugger, CodePatch, AutoDebugRecord.
- Add P16 LLM debug chain and task-level CodeTask safety.
- Add P17 run validation after implementation.
- Update test count from 244 to the current verified count.
- Add `validate-run` and dynamic matrix commands.
- Move stale P15 finalization notes into completed or superseded sections.

`docs/Q&A.md` must add a short section explaining:

- Difference between `RunEvaluationAgent` and `RunValidationAgent`.
- How to inspect a failed run.
- How to validate a run after completion.
- Which temporary artifacts can be cleaned.

## Data Flow

Workflow run:

```text
Workflow initializes ResearchState
-> state.values["workflow_settings"] = public workflow settings
-> ... -> ReviewerAgent -> RunEvaluationAgent -> RunValidationAgent -> LiteratureMemoryPersistenceAgent -> completed state
```

Existing run validation:

```text
validate-run CLI -> RunArtifactValidator -> report printed to console -> optional strict exit code
```

Dynamic validation:

```text
run command -> parse run_id/run_dir from stdout -> validate-run --run-dir <run_dir> --strict -> inspect status and artifacts
```

## Error Handling

The validator must never crash on malformed user run data. Any malformed artifact becomes a failed validation check.

Examples:

- JSON decode error in `state.json`: return `block`.
- JSON decode error in one artifact: return a check for that artifact, continue scanning other files.
- Missing artifact folder: return a warning or blocker based on whether the feature required it.
- Permission error while reading an artifact: return a blocker check with the path.

## Testing Strategy

Unit tests:

- Valid minimal run passes.
- Missing `state.json` blocks.
- Broken artifact index path blocks.
- State artifact id without file blocks.
- `AutoDebugRecord.llm_call_id` missing target blocks.
- `ExperimentResult.patch_id` missing target blocks.
- Secret-looking token in artifact blocks.
- CLI parser includes `validate-run`.
- Workflow includes `RunValidationAgent` after `RunEvaluationAgent`.

Dynamic tests:

- Run full unit suite.
- Run offline smoke and validate the produced run.
- Run retrieval evaluation smoke and validate the produced run.
- Run LLM budget-zero smoke and validate the produced run.
- Run experiment smoke and validate the produced run.
- Run real API smoke with a tiny LLM budget and validate the produced run.

Optional dynamic tests:

- Debug-loop smoke with code writes and tiny budget.

## Acceptance Criteria

P17 is complete when:

- `RunValidationReport` and `RunValidationCheck` schemas exist.
- `tools/run_artifact_validator.py` can validate a run directory without workflow context.
- `Workflow.run()` persists public workflow settings into `state.values["workflow_settings"]`.
- Workflow writes `run_validations` artifacts for normal runs.
- `app.main validate-run` validates existing run directories.
- Unit tests cover success, missing files, broken links, secret leak, CLI, and workflow integration.
- Full unit suite passes.
- At least five dynamic smoke runs are executed and validated:
  - offline minimal,
  - retrieval evaluation,
  - LLM budget-zero,
  - experiment smoke,
  - real API smoke.
- `docs/project_handoff.md` and `docs/Q&A.md` describe P17 and no longer claim P14 is the latest completed phase.
- Temporary local artifacts are not deleted automatically; they are either kept under an ignored validation output directory or explicitly documented as local evidence.

## Out Of Scope

- Enforcing validation failure as workflow abort.
- Running long training.
- Automatically deleting artifacts.
- Committing real API output or secrets.
- Changing model routes.

## Self Review

- No placeholders remain.
- P17 is a single focused feature: artifact validation and delivery hardening.
- Dynamic validation is included as commands and acceptance criteria.
- The design does not require network access in tests.
- The design does not change core research behavior or increase automatic code-writing authority.
