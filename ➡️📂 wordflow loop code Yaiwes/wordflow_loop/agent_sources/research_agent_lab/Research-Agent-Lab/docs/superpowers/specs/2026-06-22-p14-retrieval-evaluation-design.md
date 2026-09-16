# P14 Retrieval Evaluation Design

## Goal

P14 adds a retrieval-quality evaluation layer to the research workflow. It should quantify whether the literature stage is returning useful papers, whether P13 reference-network seeds actually affect the final paper set, and whether a small optional LLM judge agrees that top papers are relevant to the topic.

The output must be traceable and cheap by default. Deterministic checks run offline. LLM judging only runs when explicitly enabled.

## Scope

P14 includes:

- A schema-backed `RetrievalEvaluationReport`.
- A `RetrievalEvaluationAgent` in the main workflow.
- Deterministic retrieval metrics.
- Optional DeepSeek flash-based paper relevance judge.
- CLI flags for enabling retrieval evaluation and LLM judging.
- Integration into `RunEvaluationAgent` as warnings or blockers.
- Documentation and tests.

P14 does not include:

- Vector database integration.
- Full RAG benchmark datasets.
- Large online crawling.
- Mandatory LLM calls.
- Real external API use in unit tests.

## Architecture

Use a workflow agent, not a separate-only CLI tool.

`RetrievalEvaluationAgent` runs after `PaperTriageAgent`, because it needs both candidate papers and selected papers. It reads:

- `state.values["papers"]`
- `state.values["selected_papers"]`
- `state.values["reference_search_seeds"]`
- topic keywords from `TopicPack.keywords()`
- settings:
  - `enable_retrieval_evaluation`
  - `enable_retrieval_judge`
  - `retrieval_judge_top_k`
  - existing `enable_llm`
  - existing LLM budgets

It writes:

- `state.values["retrieval_evaluation"]`
- `state.values["retrieval_evaluation_status"]`
- `state.values["retrieval_quality_score"]`
- `artifacts/retrieval_evaluations/<eval_id>.json`

The agent is safe to run offline. LLM judge calls only happen when both conditions are true:

```text
enable_llm == True
enable_retrieval_judge == True
```

The judge uses the cheap model route. Prefer a new `retrieval_judge` route if present; otherwise fall back to the existing `paper_triage` route, which already points at the flash-class model.

## Data Flow

```text
LocalPaperLibraryAgent
→ LiteratureSearchAgent
→ PaperTriageAgent
→ RetrievalEvaluationAgent
→ LocalPaperParserAgent
→ PaperReaderAgent
→ ReferenceExtractorAgent
→ ...
→ ReviewerAgent
→ RunEvaluationAgent
→ LiteratureMemoryPersistenceAgent
```

The placement is intentional:

- `LiteratureSearchAgent` provides candidate papers.
- `PaperTriageAgent` provides selected papers.
- `RetrievalEvaluationAgent` evaluates before expensive PDF parsing and LLM method-card extraction.

## Deterministic Metrics

The offline evaluator should compute:

- `paper_count`: total candidate papers.
- `selected_paper_count`: number selected by triage.
- `source_mix`: counts by paper source, such as `local`, `reference_seed`, `arxiv`, `offline_seed`.
- `keyword_coverage`: fraction of topic keyword tokens that appear in paper titles, abstracts, or keywords.
- `selected_keyword_coverage`: same coverage computed only on selected papers.
- `reference_seed_inclusion`: whether at least one `reference_seed` paper is present when `reference_search_seeds` exists.
- `duplicate_title_rate`: approximate duplicate title ratio among candidate papers.
- `low_relevance_seed_count`: number of reference seeds below the configured score threshold.

Status rules:

- `block`: no candidate papers, or selected papers are empty when candidate papers exist.
- `needs_review`: reference seeds exist but no `reference_seed` paper enters final papers; duplicate title rate is high; keyword coverage is low.
- `pass`: no blocking issue and no warning-level issue.

Suggested thresholds:

- `keyword_coverage < 0.20`: warning.
- `selected_keyword_coverage < 0.20`: warning.
- `duplicate_title_rate > 0.30`: warning.
- no papers: blocker.
- no selected papers with non-empty candidate papers: blocker.
- reference seeds exist but none included in final papers: warning.

These thresholds should live as constants in `agents/retrieval_evaluator.py` so tests can assert stable behavior.

## Optional LLM Judge

The LLM judge evaluates top K selected papers. If selected papers are empty, it evaluates top K candidate papers.

Default:

```text
retrieval_judge_top_k = 5
```

The prompt should ask for strict JSON:

```json
{
  "judgements": [
    {
      "paper_id": "string",
      "relevance_score": 0.0,
      "decision": "relevant | borderline | irrelevant",
      "reason": "short reason"
    }
  ]
}
```

Rules:

- Do not send API key or filesystem paths.
- Do not send full paper text.
- Send title, abstract preview, keywords, source, and topic name/goals.
- Respect existing LLM call and token budgets via `llm_budget_allows()` and `record_llm_usage()`.
- Save a compact `llm_calls` artifact with status `ok`, `invalid_json`, `error`, or `skipped_*`.
- If judge output is invalid, workflow must fall back to deterministic metrics and mark judge status as warning, not crash.

LLM judge findings should affect retrieval status:

- average judge score below `0.35`: warning.
- all judged papers irrelevant: blocker.
- invalid judge output: warning.

## Schema

Create `schemas/retrieval_evaluation.py`.

Core dataclasses:

```python
@dataclass(slots=True)
class RetrievalEvaluationCheck:
    name: str
    status: str
    severity: str
    message: str
    evidence: dict = field(default_factory=dict)


@dataclass(slots=True)
class RetrievalJudgement:
    paper_id: str
    relevance_score: float
    decision: str
    reason: str = ""


@dataclass(slots=True)
class RetrievalEvaluationReport:
    status: str
    score: int
    checks: list[RetrievalEvaluationCheck] = field(default_factory=list)
    judgements: list[RetrievalJudgement] = field(default_factory=list)
    evaluation_id: str = field(default_factory=lambda: new_id("retrieval_eval"))
    created_at: str = field(default_factory=utc_now)
    summary: list[str] = field(default_factory=list)
```

## RunEvaluation Integration

`RunEvaluationAgent` should read `state.values["retrieval_evaluation"]`.

Rules:

- If retrieval status is `block`, add a blocker check.
- If retrieval status is `needs_review`, add a warning check.
- If retrieval evaluation is missing but `enable_retrieval_evaluation` is true, add a warning.
- If retrieval evaluation is disabled, do not warn.

This keeps `RunEvaluationAgent` the global quality gate while `RetrievalEvaluationAgent` owns retrieval-specific metrics.

## CLI

Add flags to `app.main run`:

```text
--enable-retrieval-evaluation
--enable-retrieval-judge
--retrieval-judge-top-k 5
```

Default behavior:

- `enable_retrieval_evaluation`: true in workflow factory unless CLI explicitly disables it would be more useful, but argparse currently has simple positive flags. To keep implementation simple and explicit, use default false for the CLI flag in P14, then revisit default-on after smoke validation.
- `enable_retrieval_judge`: false.
- `retrieval_judge_top_k`: 5.

Implementation detail:

Because the CLI flag is positive-only, P14 should keep retrieval evaluation opt-in through `--enable-retrieval-evaluation`. After it is stable, P15 or P16 can make deterministic retrieval evaluation default-on.

## Model Routing

Preferred route order for LLM judge:

1. `retrieval_judge`
2. `paper_triage`

`retrieval_judge` should be configured as a simple flash-class task in topic metadata when available. If the route is absent, `ModelRouter.route_for("paper_triage")` is acceptable for P14.

## Error Handling

The agent must not crash the workflow for retrieval-evaluation issues.

Expected handling:

- Missing `papers`: blocker report, no exception.
- Missing selected papers: blocker if papers exist.
- Missing reference seeds: pass/info for reference-seed inclusion.
- LLM disabled: deterministic-only report.
- LLM budget exhausted: judge skipped with warning.
- LLM invalid JSON: warning and deterministic report preserved.
- LLM transport error: warning unless all deterministic retrieval checks also fail.

## Testing

Unit tests must not call DeepSeek.

Test coverage should include:

- Schema defaults.
- Clean deterministic pass.
- No papers blocks.
- Papers exist but selected papers empty blocks.
- Reference seeds exist but no reference_seed source warns.
- Reference seed included passes the inclusion check.
- Duplicate title rate warning.
- Low keyword coverage warning.
- LLM judge disabled by default.
- LLM judge requires both `enable_llm` and `enable_retrieval_judge`.
- Mocked LLM judge valid JSON produces judgements.
- Mocked invalid JSON produces warning, not crash.
- `RunEvaluationAgent` consumes retrieval status.
- CLI flags parse.
- Full offline workflow can run with retrieval evaluation enabled.

## Verification

Focused tests:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_retrieval_evaluator tests.test_run_evaluator tests.test_full_research_loop
```

Full tests:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest discover -s tests -p "test*.py"
```

Offline smoke:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir data --max-papers 4 --enable-reference-expansion --max-reference-seeds 4 --enable-retrieval-evaluation
```

Controlled LLM judge smoke:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir data --max-papers 4 --enable-retrieval-evaluation --enable-retrieval-judge --enable-llm --llm-call-budget 2 --llm-token-budget 12000 --retrieval-judge-top-k 3
```

Expected artifacts:

```text
data/runs/<run_id>/artifacts/retrieval_evaluations/*.json
data/runs/<run_id>/artifacts/llm_calls/*.json  # only for LLM judge smoke
```

## Documentation

Update:

- `docs/project_handoff.md`
- Create `docs/retrieval_evaluation.md`

The docs must state clearly:

- Deterministic retrieval evaluation is opt-in in P14.
- LLM judge is opt-in and requires both `--enable-llm` and `--enable-retrieval-judge`.
- Unit tests do not call real APIs.
- Real API smoke should use low top K and small budget.

## Open Decisions Resolved

- Scope: B, deterministic retrieval evaluation plus optional LLM judge.
- LLM judge gate: requires both `--enable-llm` and `--enable-retrieval-judge`.
- Model class: flash route, preferably `retrieval_judge`, fallback to `paper_triage`.
- Default: deterministic evaluation remains CLI opt-in for P14; judge default off.

## Self-Review

- Placeholder scan: no TBD/TODO placeholders remain.
- Internal consistency: data flow places retrieval evaluation after triage and before parsing, matching required inputs.
- Scope check: one feature area only; vector DB and full benchmark harness are out of scope.
- Ambiguity check: LLM judge gates, route fallback, thresholds, and failure behavior are explicit.
