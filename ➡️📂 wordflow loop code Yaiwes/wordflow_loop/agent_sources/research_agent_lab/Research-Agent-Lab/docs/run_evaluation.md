# Run Evaluation

`RunEvaluationAgent` is a deterministic quality gate for each workflow run.

It runs after `ReviewerAgent` and writes:

- `state.values["run_evaluation_status"]`
- `state.values["run_quality_score"]`
- `artifacts/run_evaluations/<runeval_id>.json`

## Status

- `pass`: no blocking issues and score >= 85
- `needs_review`: no blocking issues, but warnings or lower score exist
- `block`: one or more blocking issues exist

## Current Checks

- literature selected papers and method cards
- unsupported evidence count
- LLM call and token budgets
- experiment execution errors and unparsed results
- experiment tree root, selected-node, width, and parent/child consistency
- reviewer status

## Recommended Use

Before increasing `--max-papers`, `--llm-call-budget`, or `--max-parallel-branches`, inspect the latest run evaluation artifact.

Do not expand budget when status is `block`.
