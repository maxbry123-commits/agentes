# P14 Retrieval Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add retrieval-quality evaluation to each opted-in workflow run, with deterministic offline metrics and an optional DeepSeek flash judge for top papers.

**Architecture:** Add `RetrievalEvaluationAgent` after `PaperTriageAgent`. It writes a structured `retrieval_evaluations/*.json` artifact and state values. Deterministic checks run without network or API. LLM judging only runs when both `--enable-llm` and `--enable-retrieval-judge` are set. `RunEvaluationAgent` consumes the retrieval report as part of the global quality gate.

**Tech Stack:** Python dataclasses, existing `Agent` / `AgentContext` / `ResearchState`, `ArtifactStore`, `ModelRouter`, `OpenAICompatibleClient`, `llm_budget`, `unittest`, `video_llava` Python environment.

---

## Confirmed Execution Parameters

- Scope is option B: deterministic retrieval evaluation plus optional LLM judge.
- Unit tests must not call real DeepSeek APIs.
- Deterministic retrieval evaluation is opt-in for P14 via `--enable-retrieval-evaluation`.
- LLM judge is opt-in and must require both `--enable-llm` and `--enable-retrieval-judge`.
- LLM judge should use `retrieval_judge` route if configured, otherwise fall back to `paper_triage`.
- Default judge top K is 5.
- No API keys, full prompts, or full paper texts should be written to artifacts.

---

## File Structure

- Create: `schemas/retrieval_evaluation.py`
  - Defines `RetrievalEvaluationCheck`, `RetrievalJudgement`, and `RetrievalEvaluationReport`.
- Create: `agents/retrieval_evaluator.py`
  - Implements deterministic metrics and optional LLM judge.
- Modify: `agents/__init__.py`
  - Exports `RetrievalEvaluationAgent`.
- Modify: `workflows/factory.py`
  - Inserts `RetrievalEvaluationAgent` after `PaperTriageAgent`.
  - Adds retrieval-evaluation settings.
- Modify: `app/main.py`
  - Adds CLI flags.
- Modify: `agents/run_evaluator.py`
  - Adds retrieval evaluation checks to the global run gate.
- Create: `tests/test_retrieval_evaluator.py`
  - Unit tests for schema, deterministic checks, LLM judge gating, mocked judge output, and artifact writing.
- Modify: `tests/test_run_evaluator.py`
  - Adds retrieval report integration tests.
- Modify: `tests/test_full_research_loop.py`
  - Adds CLI parser and offline workflow tests.
- Create: `docs/retrieval_evaluation.md`
  - Documents usage and API safety.
- Modify: `docs/project_handoff.md`
  - Updates P14 status, test count, commands, and next steps.

---

## Task 1: Retrieval Evaluation Schema

**Files:**
- Create: `schemas/retrieval_evaluation.py`
- Create/Modify: `tests/test_retrieval_evaluator.py`

- [ ] **Step 1: Write failing schema test**

Create `tests/test_retrieval_evaluator.py`:

```python
from __future__ import annotations

from unittest import TestCase, main

from schemas.retrieval_evaluation import (
    RetrievalEvaluationCheck,
    RetrievalEvaluationReport,
    RetrievalJudgement,
)


class RetrievalEvaluationSchemaTest(TestCase):
    def test_report_defaults(self):
        check = RetrievalEvaluationCheck(
            name="paper_count",
            status="pass",
            severity="info",
            message="papers found",
            evidence={"paper_count": 3},
        )
        judgement = RetrievalJudgement(
            paper_id="paper_1",
            relevance_score=0.8,
            decision="relevant",
            reason="matches trajectory prediction",
        )
        report = RetrievalEvaluationReport(
            status="pass",
            score=95,
            checks=[check],
            judgements=[judgement],
        )

        self.assertTrue(report.evaluation_id.startswith("retrieval_eval_"))
        self.assertEqual(report.status, "pass")
        self.assertEqual(report.score, 95)
        self.assertEqual(report.checks[0].name, "paper_count")
        self.assertEqual(report.judgements[0].decision, "relevant")
        self.assertEqual(report.summary, [])


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run schema test to verify it fails**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_retrieval_evaluator.RetrievalEvaluationSchemaTest
```

Expected: `ModuleNotFoundError: No module named 'schemas.retrieval_evaluation'`.

- [ ] **Step 3: Implement schema**

Create `schemas/retrieval_evaluation.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field

from schemas.base import new_id, utc_now


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
    evaluation_id: str = field(default_factory=lambda: new_id("retrieval_eval"))
    created_at: str = field(default_factory=utc_now)
    checks: list[RetrievalEvaluationCheck] = field(default_factory=list)
    judgements: list[RetrievalJudgement] = field(default_factory=list)
    blocking_issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    summary: list[str] = field(default_factory=list)
```

- [ ] **Step 4: Run schema test**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_retrieval_evaluator.RetrievalEvaluationSchemaTest
```

Expected: `OK`.

---

## Task 2: Deterministic RetrievalEvaluationAgent

**Files:**
- Create: `agents/retrieval_evaluator.py`
- Modify: `tests/test_retrieval_evaluator.py`

- [ ] **Step 1: Add deterministic-agent tests**

Append to `tests/test_retrieval_evaluator.py`:

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from agents.retrieval_evaluator import RetrievalEvaluationAgent
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState
from schemas.topic_pack import TopicPack


def _topic() -> TopicPack:
    return TopicPack(
        topic_name="retrieval_eval_test",
        search_seeds={"keywords": ["trajectory prediction", "diffusion", "pedestrian"]},
    )


def _context(tmp: str, settings: dict | None = None) -> AgentContext:
    return AgentContext(
        artifact_store=ArtifactStore(Path(tmp)),
        memory_store=None,  # type: ignore
        tool_registry=None,  # type: ignore
        settings=settings or {},
    )


class RetrievalEvaluationAgentDeterministicTest(TestCase):
    def test_passes_clean_retrieval_state(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "papers": [
                    {
                        "paper_id": "p1",
                        "title": "Diffusion Models for Pedestrian Trajectory Prediction",
                        "abstract": "Trajectory prediction with diffusion for pedestrians.",
                        "source": "local",
                        "keywords": ["trajectory", "diffusion"],
                    },
                    {
                        "paper_id": "p2",
                        "title": "Language Conditioned Motion Forecasting",
                        "abstract": "Pedestrian motion forecasting.",
                        "source": "reference_seed",
                        "keywords": ["motion", "forecasting"],
                    },
                ],
                "selected_papers": [
                    {
                        "paper_id": "p1",
                        "title": "Diffusion Models for Pedestrian Trajectory Prediction",
                        "abstract": "Trajectory prediction with diffusion for pedestrians.",
                        "source": "local",
                        "keywords": ["trajectory", "diffusion"],
                    },
                ],
                "reference_search_seeds": [
                    {"query": "Language Conditioned Motion Forecasting", "relevance_score": 0.8}
                ],
            })

            result = RetrievalEvaluationAgent().run(state, _context(tmp))

            report = state.values["retrieval_evaluation"]
            self.assertEqual(report["status"], "pass")
            self.assertGreaterEqual(report["score"], 85)
            self.assertIn("retrieval_evaluations", result.artifacts)
            self.assertEqual(state.values["retrieval_evaluation_status"], "pass")

    def test_blocks_when_no_papers(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values["papers"] = []
            state.values["selected_papers"] = []

            RetrievalEvaluationAgent().run(state, _context(tmp))

            report = state.values["retrieval_evaluation"]
            self.assertEqual(report["status"], "block")
            self.assertTrue(any("no candidate papers" in issue for issue in report["blocking_issues"]))

    def test_blocks_when_papers_exist_but_none_selected(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values["papers"] = [{"paper_id": "p1", "title": "Trajectory Prediction", "source": "local"}]
            state.values["selected_papers"] = []

            RetrievalEvaluationAgent().run(state, _context(tmp))

            report = state.values["retrieval_evaluation"]
            self.assertEqual(report["status"], "block")
            self.assertTrue(any("no selected papers" in issue for issue in report["blocking_issues"]))

    def test_warns_when_reference_seeds_not_included(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "papers": [{"paper_id": "p1", "title": "Trajectory Prediction", "source": "local"}],
                "selected_papers": [{"paper_id": "p1", "title": "Trajectory Prediction", "source": "local"}],
                "reference_search_seeds": [{"query": "Language Conditioned Motion", "relevance_score": 0.9}],
            })

            RetrievalEvaluationAgent().run(state, _context(tmp))

            report = state.values["retrieval_evaluation"]
            self.assertEqual(report["status"], "needs_review")
            self.assertTrue(any("reference seeds" in warning for warning in report["warnings"]))

    def test_warns_on_duplicate_title_rate(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "papers": [
                    {"paper_id": "p1", "title": "Same Title", "source": "local"},
                    {"paper_id": "p2", "title": "Same Title", "source": "local"},
                    {"paper_id": "p3", "title": "Different Trajectory Title", "source": "local"},
                ],
                "selected_papers": [{"paper_id": "p3", "title": "Different Trajectory Title", "source": "local"}],
            })

            RetrievalEvaluationAgent().run(state, _context(tmp))

            report = state.values["retrieval_evaluation"]
            duplicate_check = next(c for c in report["checks"] if c["name"] == "duplicate_title_rate")
            self.assertEqual(duplicate_check["status"], "warn")

    def test_warns_on_low_keyword_coverage(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "papers": [{"paper_id": "p1", "title": "Image Classification Survey", "source": "local"}],
                "selected_papers": [{"paper_id": "p1", "title": "Image Classification Survey", "source": "local"}],
            })

            RetrievalEvaluationAgent().run(state, _context(tmp))

            report = state.values["retrieval_evaluation"]
            coverage_check = next(c for c in report["checks"] if c["name"] == "keyword_coverage")
            self.assertEqual(coverage_check["status"], "warn")
```

- [ ] **Step 2: Run deterministic tests to verify they fail**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_retrieval_evaluator.RetrievalEvaluationAgentDeterministicTest
```

Expected: `ModuleNotFoundError: No module named 'agents.retrieval_evaluator'`.

- [ ] **Step 3: Implement deterministic agent**

Create `agents/retrieval_evaluator.py`:

```python
from __future__ import annotations

from dataclasses import asdict
import json
import re
from collections import Counter
from typing import Any

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from schemas.retrieval_evaluation import (
    RetrievalEvaluationCheck,
    RetrievalEvaluationReport,
    RetrievalJudgement,
)
from tools.llm_budget import llm_budget_allows, record_llm_usage
from tools.llm_client import OpenAICompatibleClient, extract_json_object
from tools.model_router import ModelRouter


KEYWORD_COVERAGE_WARN = 0.20
DUPLICATE_TITLE_RATE_WARN = 0.30
LOW_REFERENCE_SEED_SCORE = 0.30
JUDGE_AVERAGE_WARN = 0.35


class RetrievalEvaluationAgent(Agent):
    name = "retrieval_evaluator"

    def __init__(self):
        super().__init__()
        self.llm_client = OpenAICompatibleClient()

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        papers = _as_list(state.values.get("papers"))
        selected = _as_list(state.values.get("selected_papers"))
        reference_seeds = _as_list(state.values.get("reference_search_seeds"))
        keywords = state.topic.keywords()

        checks: list[RetrievalEvaluationCheck] = []
        checks.extend(_paper_count_checks(papers, selected))
        checks.extend(_source_mix_checks(papers))
        checks.extend(_keyword_checks(papers, selected, keywords))
        checks.extend(_reference_seed_checks(papers, reference_seeds))
        checks.extend(_duplicate_checks(papers))

        judgements: list[RetrievalJudgement] = []
        if context.settings.get("enable_llm") and context.settings.get("enable_retrieval_judge"):
            judge_checks, judgements = self._judge_top_papers(state, context, papers, selected)
            checks.extend(judge_checks)
        else:
            checks.append(RetrievalEvaluationCheck(
                name="llm_retrieval_judge",
                status="pass",
                severity="info",
                message="LLM retrieval judge disabled",
                evidence={
                    "enable_llm": bool(context.settings.get("enable_llm")),
                    "enable_retrieval_judge": bool(context.settings.get("enable_retrieval_judge")),
                },
            ))

        blocking = [c.message for c in checks if c.status == "fail" and c.severity == "blocker"]
        warnings = [c.message for c in checks if c.status in {"warn", "fail"} and c.severity != "blocker"]
        score = _score(checks)
        status = "block" if blocking else ("needs_review" if warnings or score < 85 else "pass")
        report = RetrievalEvaluationReport(
            status=status,
            score=score,
            checks=checks,
            judgements=judgements,
            blocking_issues=blocking,
            warnings=warnings,
            summary=[
                f"status={status}",
                f"score={score}",
                f"papers={len(papers)}",
                f"selected={len(selected)}",
                f"judgements={len(judgements)}",
            ],
        )
        payload = asdict(report)
        context.artifact_store.save_json(
            state.run_id, "retrieval_evaluations", report.evaluation_id, payload
        )
        state.values["retrieval_evaluation"] = payload
        state.values["retrieval_evaluation_status"] = status
        state.values["retrieval_quality_score"] = score
        return AgentResult(
            notes=[f"retrieval evaluation status={status} score={score}"],
            artifacts={"retrieval_evaluations": [report.evaluation_id]},
            values={
                "retrieval_evaluation": payload,
                "retrieval_evaluation_status": status,
                "retrieval_quality_score": score,
            },
        )

    def _judge_top_papers(
        self,
        state: ResearchState,
        context: AgentContext,
        papers: list[dict[str, Any]],
        selected: list[dict[str, Any]],
    ) -> tuple[list[RetrievalEvaluationCheck], list[RetrievalJudgement]]:
        top_k = int(context.settings.get("retrieval_judge_top_k", 5) or 5)
        candidates = (selected or papers)[:max(1, top_k)]
        if not candidates:
            return [RetrievalEvaluationCheck(
                name="llm_retrieval_judge",
                status="warn",
                severity="warning",
                message="LLM judge skipped because no papers are available",
                evidence={"top_k": top_k},
            )], []

        allowed, reason = llm_budget_allows(state, context.settings)
        if not allowed:
            _save_judge_call_record(context, state, "skipped_" + reason, reason, "", {})
            return [RetrievalEvaluationCheck(
                name="llm_retrieval_judge",
                status="warn",
                severity="warning",
                message=f"LLM retrieval judge skipped: {reason}",
                evidence={"reason": reason},
            )], []

        route = _retrieval_judge_route(state)
        messages = _judge_messages(state, candidates)
        response = self.llm_client.chat(route, messages, temperature=0.1, max_tokens=1200)
        record_llm_usage(state, response.usage)
        if not response.ok:
            _save_judge_call_record(context, state, "error", response.error, route.model, response.usage)
            return [RetrievalEvaluationCheck(
                name="llm_retrieval_judge",
                status="warn",
                severity="warning",
                message=f"LLM retrieval judge error: {response.error[:120]}",
                evidence={"provider": route.provider, "model": route.model},
            )], []

        payload = extract_json_object(response.text)
        if not isinstance(payload, dict) or not isinstance(payload.get("judgements"), list):
            _save_judge_call_record(context, state, "invalid_json", "missing judgements", route.model, response.usage)
            return [RetrievalEvaluationCheck(
                name="llm_retrieval_judge",
                status="warn",
                severity="warning",
                message="LLM retrieval judge returned invalid JSON",
                evidence={"provider": route.provider, "model": route.model},
            )], []

        judgements = _parse_judgements(payload.get("judgements", []))
        _save_judge_call_record(context, state, "ok", "", route.model, response.usage)
        checks = [_judge_quality_check(judgements)]
        return checks, judgements
```

Append helper functions in the same file:

```python
def _as_list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [item for item in value.values() if isinstance(item, dict)]
    return []


def _paper_count_checks(papers: list[dict[str, Any]], selected: list[dict[str, Any]]) -> list[RetrievalEvaluationCheck]:
    return [
        RetrievalEvaluationCheck(
            name="paper_count",
            status="pass" if papers else "fail",
            severity="blocker",
            message="candidate papers found" if papers else "no candidate papers found",
            evidence={"paper_count": len(papers)},
        ),
        RetrievalEvaluationCheck(
            name="selected_paper_count",
            status="pass" if selected else "fail",
            severity="blocker" if papers else "warning",
            message="selected papers found" if selected else "no selected papers found",
            evidence={"selected_paper_count": len(selected), "paper_count": len(papers)},
        ),
    ]


def _source_mix_checks(papers: list[dict[str, Any]]) -> list[RetrievalEvaluationCheck]:
    mix = Counter(str(p.get("source", "unknown") or "unknown") for p in papers)
    return [RetrievalEvaluationCheck(
        name="source_mix",
        status="pass",
        severity="info",
        message="paper source mix recorded",
        evidence={"source_mix": dict(mix)},
    )]


def _keyword_checks(
    papers: list[dict[str, Any]], selected: list[dict[str, Any]], keywords: list[str]
) -> list[RetrievalEvaluationCheck]:
    coverage = _keyword_coverage(papers, keywords)
    selected_coverage = _keyword_coverage(selected, keywords)
    return [
        RetrievalEvaluationCheck(
            name="keyword_coverage",
            status="pass" if coverage >= KEYWORD_COVERAGE_WARN else "warn",
            severity="warning",
            message=f"keyword coverage={coverage:.2f}",
            evidence={"keyword_coverage": coverage},
        ),
        RetrievalEvaluationCheck(
            name="selected_keyword_coverage",
            status="pass" if selected_coverage >= KEYWORD_COVERAGE_WARN else "warn",
            severity="warning",
            message=f"selected keyword coverage={selected_coverage:.2f}",
            evidence={"selected_keyword_coverage": selected_coverage},
        ),
    ]


def _reference_seed_checks(
    papers: list[dict[str, Any]], reference_seeds: list[dict[str, Any]]
) -> list[RetrievalEvaluationCheck]:
    if not reference_seeds:
        return [RetrievalEvaluationCheck(
            name="reference_seed_inclusion",
            status="pass",
            severity="info",
            message="no reference search seeds available",
            evidence={"reference_seed_count": 0},
        )]
    included = sum(1 for p in papers if str(p.get("source", "")) == "reference_seed")
    low_score = sum(
        1 for seed in reference_seeds
        if float(seed.get("relevance_score", 0.0) or 0.0) < LOW_REFERENCE_SEED_SCORE
    )
    return [
        RetrievalEvaluationCheck(
            name="reference_seed_inclusion",
            status="pass" if included > 0 else "warn",
            severity="warning",
            message="reference seeds included in papers" if included else "reference seeds exist but no reference_seed paper is included",
            evidence={"reference_seed_count": len(reference_seeds), "included_reference_seed_papers": included},
        ),
        RetrievalEvaluationCheck(
            name="low_relevance_seed_count",
            status="pass" if low_score == 0 else "warn",
            severity="warning",
            message="reference seed scores look usable" if low_score == 0 else f"{low_score} low relevance reference seed(s)",
            evidence={"low_relevance_seed_count": low_score},
        ),
    ]


def _duplicate_checks(papers: list[dict[str, Any]]) -> list[RetrievalEvaluationCheck]:
    titles = [str(p.get("title", "")).strip().lower() for p in papers if str(p.get("title", "")).strip()]
    duplicate_count = len(titles) - len(set(titles))
    rate = duplicate_count / max(1, len(titles))
    return [RetrievalEvaluationCheck(
        name="duplicate_title_rate",
        status="pass" if rate <= DUPLICATE_TITLE_RATE_WARN else "warn",
        severity="warning",
        message=f"duplicate title rate={rate:.2f}",
        evidence={"duplicate_title_rate": rate, "duplicate_title_count": duplicate_count},
    )]


def _keyword_coverage(papers: list[dict[str, Any]], keywords: list[str]) -> float:
    tokens = _keyword_tokens(keywords)
    if not tokens:
        return 1.0
    text = " ".join(_paper_text(paper) for paper in papers).lower()
    if not text:
        return 0.0
    hits = sum(1 for token in tokens if re.search(r"\b" + re.escape(token) + r"\b", text))
    return round(hits / len(tokens), 4)


def _keyword_tokens(keywords: list[str]) -> list[str]:
    tokens: set[str] = set()
    for keyword in keywords:
        for token in str(keyword).lower().split():
            token = token.strip(".,;:!?()[]{}\"'")
            if len(token) >= 3:
                tokens.add(token)
    return sorted(tokens)


def _paper_text(paper: dict[str, Any]) -> str:
    kw = paper.get("keywords", [])
    kw_text = " ".join(str(item) for item in kw) if isinstance(kw, list) else str(kw)
    return " ".join([
        str(paper.get("title", "")),
        str(paper.get("abstract", "")),
        kw_text,
    ])


def _retrieval_judge_route(state: ResearchState):
    router = ModelRouter(state.topic)
    route = router.route_for("retrieval_judge")
    if route.provider in {"offline", "local", "rule_based"} or route.model == "rule_based":
        return router.route_for("paper_triage")
    return route


def _judge_messages(state: ResearchState, papers: list[dict[str, Any]]) -> list[dict[str, str]]:
    compact = []
    for paper in papers:
        compact.append({
            "paper_id": str(paper.get("paper_id", "")),
            "title": str(paper.get("title", ""))[:300],
            "abstract": str(paper.get("abstract", ""))[:900],
            "keywords": paper.get("keywords", []),
            "source": paper.get("source", ""),
        })
    return [
        {"role": "system", "content": (
            "You judge whether retrieved papers are relevant to a research topic. "
            "Return exactly one JSON object with key judgements. Each judgement must include "
            "paper_id, relevance_score from 0.0 to 1.0, decision as relevant/borderline/irrelevant, and reason."
        )},
        {"role": "user", "content": json.dumps({
            "topic": state.topic.topic_name,
            "keywords": state.topic.keywords(),
            "research_goal": state.topic.research_goal,
            "papers": compact,
        }, ensure_ascii=False)},
    ]


def _parse_judgements(rows: list[Any]) -> list[RetrievalJudgement]:
    result: list[RetrievalJudgement] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        paper_id = str(row.get("paper_id", ""))
        if not paper_id:
            continue
        try:
            score = float(row.get("relevance_score", 0.0) or 0.0)
        except (TypeError, ValueError):
            score = 0.0
        decision = str(row.get("decision", "borderline"))
        if decision not in {"relevant", "borderline", "irrelevant"}:
            decision = "borderline"
        result.append(RetrievalJudgement(
            paper_id=paper_id,
            relevance_score=max(0.0, min(1.0, score)),
            decision=decision,
            reason=str(row.get("reason", ""))[:300],
        ))
    return result


def _judge_quality_check(judgements: list[RetrievalJudgement]) -> RetrievalEvaluationCheck:
    if not judgements:
        return RetrievalEvaluationCheck(
            name="llm_retrieval_judge",
            status="warn",
            severity="warning",
            message="LLM retrieval judge produced no usable judgements",
            evidence={"judgement_count": 0},
        )
    average = sum(j.relevance_score for j in judgements) / len(judgements)
    irrelevant = sum(1 for j in judgements if j.decision == "irrelevant")
    all_irrelevant = irrelevant == len(judgements)
    status = "fail" if all_irrelevant else ("warn" if average < JUDGE_AVERAGE_WARN else "pass")
    severity = "blocker" if all_irrelevant else "warning"
    return RetrievalEvaluationCheck(
        name="llm_retrieval_judge",
        status=status,
        severity=severity,
        message=f"LLM retrieval judge average relevance={average:.2f}",
        evidence={
            "average_relevance_score": round(average, 4),
            "judgement_count": len(judgements),
            "irrelevant_count": irrelevant,
        },
    )


def _save_judge_call_record(
    context: AgentContext,
    state: ResearchState,
    status: str,
    error: str,
    model: str,
    usage: dict[str, Any],
) -> None:
    call_id = f"retrieval_judge_{len(context.artifact_store.list_artifacts(state.run_id, 'llm_calls')) + 1}"
    context.artifact_store.save_json(state.run_id, "llm_calls", call_id, {
        "agent": "retrieval_judge",
        "status": status,
        "model": model,
        "error": error[:300],
        "usage": usage,
    })


def _score(checks: list[RetrievalEvaluationCheck]) -> int:
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

- [ ] **Step 4: Run deterministic tests**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_retrieval_evaluator.RetrievalEvaluationAgentDeterministicTest
```

Expected: deterministic tests pass.

---

## Task 3: Optional LLM Judge With Mocked Client

**Files:**
- Modify: `tests/test_retrieval_evaluator.py`
- Modify: `agents/retrieval_evaluator.py` if needed.

- [ ] **Step 1: Add LLM judge tests**

Append to `tests/test_retrieval_evaluator.py`:

```python
from tools.llm_client import LLMResponse


class _FakeJudgeClient:
    def __init__(self, response: LLMResponse):
        self.response = response
        self.calls = 0

    def chat(self, route, messages, temperature=0.2, max_tokens=1200, base_url=None):
        self.calls += 1
        return self.response


class RetrievalEvaluationAgentJudgeTest(TestCase):
    def test_judge_not_called_without_both_flags(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "papers": [{"paper_id": "p1", "title": "Trajectory Prediction", "source": "local"}],
                "selected_papers": [{"paper_id": "p1", "title": "Trajectory Prediction", "source": "local"}],
            })
            fake = _FakeJudgeClient(LLMResponse(ok=True, text="{}"))
            agent = RetrievalEvaluationAgent()
            agent.llm_client = fake

            agent.run(state, _context(tmp, {"enable_llm": True, "enable_retrieval_judge": False}))

            self.assertEqual(fake.calls, 0)
            checks = state.values["retrieval_evaluation"]["checks"]
            judge_check = next(c for c in checks if c["name"] == "llm_retrieval_judge")
            self.assertEqual(judge_check["severity"], "info")

    def test_valid_judge_json_adds_judgements(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "papers": [{"paper_id": "p1", "title": "Trajectory Prediction", "source": "local"}],
                "selected_papers": [{"paper_id": "p1", "title": "Trajectory Prediction", "source": "local"}],
            })
            fake = _FakeJudgeClient(LLMResponse(
                ok=True,
                text='{"judgements":[{"paper_id":"p1","relevance_score":0.9,"decision":"relevant","reason":"matches"}]}',
                usage={"total_tokens": 123},
                provider="deepseek",
                model="deepseek-v4-flash",
            ))
            agent = RetrievalEvaluationAgent()
            agent.llm_client = fake

            agent.run(state, _context(tmp, {
                "enable_llm": True,
                "enable_retrieval_judge": True,
                "llm_call_budget": 2,
                "llm_token_budget": 10000,
                "retrieval_judge_top_k": 1,
            }))

            report = state.values["retrieval_evaluation"]
            self.assertEqual(fake.calls, 1)
            self.assertEqual(len(report["judgements"]), 1)
            self.assertEqual(report["judgements"][0]["decision"], "relevant")

    def test_invalid_judge_json_warns_without_crash(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "papers": [{"paper_id": "p1", "title": "Trajectory Prediction", "source": "local"}],
                "selected_papers": [{"paper_id": "p1", "title": "Trajectory Prediction", "source": "local"}],
            })
            fake = _FakeJudgeClient(LLMResponse(ok=True, text="not json", usage={"total_tokens": 10}))
            agent = RetrievalEvaluationAgent()
            agent.llm_client = fake

            agent.run(state, _context(tmp, {
                "enable_llm": True,
                "enable_retrieval_judge": True,
                "llm_call_budget": 2,
                "llm_token_budget": 10000,
            }))

            report = state.values["retrieval_evaluation"]
            self.assertEqual(report["status"], "needs_review")
            self.assertTrue(any("invalid JSON" in warning for warning in report["warnings"]))

    def test_all_irrelevant_judge_blocks(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "papers": [{"paper_id": "p1", "title": "Image Classification", "source": "local"}],
                "selected_papers": [{"paper_id": "p1", "title": "Image Classification", "source": "local"}],
            })
            fake = _FakeJudgeClient(LLMResponse(
                ok=True,
                text='{"judgements":[{"paper_id":"p1","relevance_score":0.1,"decision":"irrelevant","reason":"unrelated"}]}',
                usage={"total_tokens": 20},
            ))
            agent = RetrievalEvaluationAgent()
            agent.llm_client = fake

            agent.run(state, _context(tmp, {
                "enable_llm": True,
                "enable_retrieval_judge": True,
                "llm_call_budget": 2,
                "llm_token_budget": 10000,
            }))

            report = state.values["retrieval_evaluation"]
            self.assertEqual(report["status"], "block")
            self.assertTrue(any("average relevance" in issue for issue in report["blocking_issues"]))
```

- [ ] **Step 2: Run judge tests**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_retrieval_evaluator.RetrievalEvaluationAgentJudgeTest
```

Expected: judge tests pass without external API calls.

---

## Task 4: Workflow And CLI Integration

**Files:**
- Modify: `agents/__init__.py`
- Modify: `workflows/factory.py`
- Modify: `app/main.py`
- Modify: `tests/test_full_research_loop.py`

- [ ] **Step 1: Add CLI parser tests**

Append to `tests/test_full_research_loop.py`:

```python
class RetrievalEvaluationCliParserTest(TestCase):
    def test_retrieval_evaluation_flags_parse(self):
        from app.main import build_parser
        parser = build_parser()
        args = parser.parse_args([
            "run",
            "--topic", "topics/intent_led_virat.json",
            "--enable-retrieval-evaluation",
            "--enable-retrieval-judge",
            "--retrieval-judge-top-k", "3",
        ])

        self.assertTrue(args.enable_retrieval_evaluation)
        self.assertTrue(args.enable_retrieval_judge)
        self.assertEqual(args.retrieval_judge_top_k, 3)
```

- [ ] **Step 2: Run parser test to verify it fails**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_full_research_loop.RetrievalEvaluationCliParserTest
```

Expected: parser rejects `--enable-retrieval-evaluation`.

- [ ] **Step 3: Export agent**

Modify `agents/__init__.py`:

```python
from agents.retrieval_evaluator import RetrievalEvaluationAgent
```

Add `"RetrievalEvaluationAgent"` to `__all__`.

- [ ] **Step 4: Insert agent into workflow**

Modify `workflows/factory.py` imports:

```python
    RetrievalEvaluationAgent,
```

Add parameters to `build_full_research_workflow()`:

```python
    enable_retrieval_evaluation: bool = False,
    enable_retrieval_judge: bool = False,
    retrieval_judge_top_k: int = 5,
```

Insert after `PaperTriageAgent()`:

```python
        PaperTriageAgent(),
```

then:

```python
    if enable_retrieval_evaluation:
        agents.append(RetrievalEvaluationAgent())
```

Because the current file builds an initial list literal, make the first part explicit:

```python
    agents: list = [
        ResearchManagerAgent(),
        LocalPaperLibraryAgent(),
        LiteratureSearchAgent(lit_memory_store=literature_memory_store),
        PaperTriageAgent(),
    ]
    if enable_retrieval_evaluation:
        agents.append(RetrievalEvaluationAgent())
    agents.extend([
        LocalPaperParserAgent(),
        PaperReaderAgent(),
        ReferenceExtractorAgent(),
        EvidenceCheckerAgent(),
        MethodCardExtractorAgent(),
        SynthesisAgent(),
        CodebaseAnalyzerAgent(),
        MethodCardRetrieverAgent(lit_memory_store=literature_memory_store),
        OpportunityAgent(),
        ExperimentPlannerAgent(),
    ])
```

Add settings:

```python
            "enable_retrieval_evaluation": enable_retrieval_evaluation,
            "enable_retrieval_judge": enable_retrieval_judge,
            "retrieval_judge_top_k": retrieval_judge_top_k,
```

- [ ] **Step 5: Add CLI flags**

Modify `app/main.py` in `build_parser()`:

```python
    run_parser.add_argument(
        "--enable-retrieval-evaluation",
        action="store_true",
        help="Evaluate literature retrieval quality and write retrieval_evaluations artifacts",
    )
    run_parser.add_argument(
        "--enable-retrieval-judge",
        action="store_true",
        help="Allow optional LLM judge for top retrieved papers; requires --enable-llm",
    )
    run_parser.add_argument(
        "--retrieval-judge-top-k",
        type=int,
        default=5,
        help="Maximum selected papers to judge when retrieval judge is enabled",
    )
```

Pass through in `run_workflow()`:

```python
        enable_retrieval_evaluation=args.enable_retrieval_evaluation,
        enable_retrieval_judge=args.enable_retrieval_judge,
        retrieval_judge_top_k=args.retrieval_judge_top_k,
```

- [ ] **Step 6: Run parser test**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_full_research_loop.RetrievalEvaluationCliParserTest
```

Expected: `OK`.

---

## Task 5: RunEvaluationAgent Integration

**Files:**
- Modify: `agents/run_evaluator.py`
- Modify: `tests/test_run_evaluator.py`

- [ ] **Step 1: Add run evaluator tests**

Append to `tests/test_run_evaluator.py`:

```python
class RunEvaluationRetrievalIntegrationTest(TestCase):
    def test_retrieval_block_status_blocks_run(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
                "retrieval_evaluation": {
                    "status": "block",
                    "score": 60,
                    "blocking_issues": ["no candidate papers found"],
                    "warnings": [],
                },
            })

            RunEvaluationAgent().run(state, _context(tmp, {"enable_retrieval_evaluation": True}))

            report = state.values["run_evaluation"]
            self.assertEqual(report["status"], "block")
            self.assertTrue(any("retrieval evaluation blocked" in item for item in report["blocking_issues"]))

    def test_retrieval_needs_review_warns_run(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
                "retrieval_evaluation": {
                    "status": "needs_review",
                    "score": 80,
                    "blocking_issues": [],
                    "warnings": ["low keyword coverage"],
                },
            })

            RunEvaluationAgent().run(state, _context(tmp, {"enable_retrieval_evaluation": True}))

            report = state.values["run_evaluation"]
            checks = report["checks"]
            retrieval_check = next(c for c in checks if c["name"] == "retrieval_evaluation")
            self.assertEqual(retrieval_check["status"], "warn")

    def test_missing_retrieval_report_warns_only_when_enabled(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "selected_paper_count": 1,
                "method_card_count": 1,
                "review_status": "pass",
            })

            RunEvaluationAgent().run(state, _context(tmp, {"enable_retrieval_evaluation": True}))

            checks = state.values["run_evaluation"]["checks"]
            retrieval_check = next(c for c in checks if c["name"] == "retrieval_evaluation")
            self.assertEqual(retrieval_check["status"], "warn")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_run_evaluator.RunEvaluationRetrievalIntegrationTest
```

Expected: no `retrieval_evaluation` check exists.

- [ ] **Step 3: Implement retrieval checks**

Modify `agents/run_evaluator.py`.

In `RunEvaluationAgent.run()`, after `_literature_checks(state)`:

```python
        checks.extend(_retrieval_evaluation_checks(state, context.settings))
```

Add helper before `_budget_checks()`:

```python
def _retrieval_evaluation_checks(
    state: ResearchState, settings: dict[str, Any]
) -> list[RunEvaluationCheck]:
    enabled = bool(settings.get("enable_retrieval_evaluation"))
    report = state.values.get("retrieval_evaluation")
    if not enabled and not isinstance(report, dict):
        return []
    if enabled and not isinstance(report, dict):
        return [RunEvaluationCheck(
            name="retrieval_evaluation",
            status="warn",
            severity="warning",
            message="retrieval evaluation was enabled but no report was produced",
            evidence={"enable_retrieval_evaluation": enabled},
        )]
    status = str(report.get("status", "unknown"))
    score = int(report.get("score", 0) or 0)
    if status == "block":
        return [RunEvaluationCheck(
            name="retrieval_evaluation",
            status="fail",
            severity="blocker",
            message=f"retrieval evaluation blocked run: score={score}",
            evidence={
                "retrieval_status": status,
                "retrieval_score": score,
                "blocking_issues": report.get("blocking_issues", []),
            },
        )]
    if status == "needs_review":
        return [RunEvaluationCheck(
            name="retrieval_evaluation",
            status="warn",
            severity="warning",
            message=f"retrieval evaluation needs review: score={score}",
            evidence={
                "retrieval_status": status,
                "retrieval_score": score,
                "warnings": report.get("warnings", []),
            },
        )]
    return [RunEvaluationCheck(
        name="retrieval_evaluation",
        status="pass",
        severity="info",
        message=f"retrieval evaluation status={status} score={score}",
        evidence={"retrieval_status": status, "retrieval_score": score},
    )]
```

- [ ] **Step 4: Run run evaluator tests**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_run_evaluator.RunEvaluationRetrievalIntegrationTest
```

Expected: `OK`.

---

## Task 6: Offline Workflow Test

**Files:**
- Modify: `tests/test_full_research_loop.py`

- [ ] **Step 1: Add workflow test**

Add this test:

```python
class RetrievalEvaluationWorkflowTest(TestCase):
    def test_offline_workflow_can_write_retrieval_evaluation(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        from core.artifact_store import ArtifactStore
        from core.run_logger import RunLogger
        from memory.sqlite_memory import SQLiteMemoryStore
        from schemas.topic_pack import TopicPack
        from tools.tool_registry import ToolRegistry
        from workflows.factory import build_full_research_workflow

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            store = ArtifactStore(tmp_path / "runs")
            topic = TopicPack(
                topic_name="workflow_retrieval_eval",
                search_seeds={"keywords": ["trajectory prediction", "diffusion"]},
            )
            workflow = build_full_research_workflow(
                artifact_store=store,
                memory_store=SQLiteMemoryStore(tmp_path / "memory.sqlite3"),
                tool_registry=ToolRegistry(),
                logger=RunLogger(),
                max_papers=2,
                enable_retrieval_evaluation=True,
            )

            state = workflow.run(topic)
            run_dir = store.run_dir(state.run_id)

            self.assertIn("retrieval_evaluation", state.values)
            self.assertTrue((run_dir / "artifacts" / "retrieval_evaluations").exists())
            self.assertGreaterEqual(
                len(list((run_dir / "artifacts" / "retrieval_evaluations").glob("*.json"))),
                1,
            )
```

- [ ] **Step 2: Run workflow test**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_full_research_loop.RetrievalEvaluationWorkflowTest
```

Expected: `OK`.

---

## Task 7: Documentation And Handoff

**Files:**
- Create: `docs/retrieval_evaluation.md`
- Modify: `docs/project_handoff.md`

- [ ] **Step 1: Create retrieval evaluation docs**

Create `docs/retrieval_evaluation.md`:

```markdown
# Retrieval Evaluation

`RetrievalEvaluationAgent` measures literature retrieval quality.

It is opt-in in P14:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir data --max-papers 4 --enable-retrieval-evaluation
```

## Outputs

- `state.values["retrieval_evaluation"]`
- `state.values["retrieval_evaluation_status"]`
- `state.values["retrieval_quality_score"]`
- `artifacts/retrieval_evaluations/*.json`

## Deterministic Checks

- candidate paper count
- selected paper count
- source mix
- topic keyword coverage
- selected-paper keyword coverage
- reference seed inclusion
- duplicate title rate
- low relevance reference seed count

## Optional LLM Judge

The judge is disabled by default. It only runs when both flags are present:

```powershell
--enable-llm --enable-retrieval-judge
```

Use a small top K and budget:

```powershell
--retrieval-judge-top-k 3 --llm-call-budget 2 --llm-token-budget 12000
```

Unit tests mock the judge and do not call real APIs.
```

- [ ] **Step 2: Update project handoff**

Update `docs/project_handoff.md`:

- Change update line to `更新时间：2026-06-22（P14 完成）` only after all verification passes.
- Add `RetrievalEvaluationAgent` to implemented agents.
- Add `RetrievalEvaluationReport`, `RetrievalEvaluationCheck`, and `RetrievalJudgement` to structured artifacts.
- Add `docs/retrieval_evaluation.md` to docs section if present.
- Add common commands:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir data --max-papers 4 --enable-retrieval-evaluation
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir data --max-papers 4 --enable-retrieval-evaluation --enable-retrieval-judge --enable-llm --llm-call-budget 2 --llm-token-budget 12000 --retrieval-judge-top-k 3
```

- Update test count after full test suite passes.
- Move P14 from next steps to completed.
- Keep P15 finalization check as next step.

---

## Task 8: Verification

**Files:**
- All files touched above.

- [ ] **Step 1: Run focused tests**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest tests.test_retrieval_evaluator tests.test_run_evaluator tests.test_full_research_loop
```

Expected: all focused tests pass.

- [ ] **Step 2: Run full test suite**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m unittest discover -s tests -p "test*.py"
```

Expected: all tests pass. Baseline before P14 plan writing was `Ran 226 tests ... OK`.

- [ ] **Step 3: Run offline smoke**

Run:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir data --max-papers 4 --enable-reference-expansion --max-reference-seeds 4 --enable-retrieval-evaluation
```

Expected:

```text
stage=completed
run_dir=data\runs\<run_id>
```

Inspect:

```text
data/runs/<run_id>/artifacts/retrieval_evaluations/*.json
```

Expected JSON includes `status`, `score`, `checks`, and no `judgements` unless LLM judge is enabled.

- [ ] **Step 4: Optional controlled LLM judge smoke**

Run only after offline smoke passes:

```powershell
D:\Develop_Tools\Anaconda3\envs\video_llava\python.exe -m app.main run --topic topics\intent_led_virat.json --data-dir data --max-papers 4 --enable-retrieval-evaluation --enable-retrieval-judge --enable-llm --llm-call-budget 2 --llm-token-budget 12000 --retrieval-judge-top-k 3
```

Expected:

- workflow completes;
- `artifacts/retrieval_evaluations/*.json` exists;
- `artifacts/llm_calls/*.json` has compact judge record;
- no API key appears in artifacts;
- if LLM output is invalid, status is `needs_review`, not crash.

---

## Self-Review

- Spec coverage: Covers confirmed option B: deterministic retrieval evaluation plus optional LLM judge.
- Placeholder scan: No `TBD`, `TODO`, or vague placeholder remains in implementation steps.
- Type consistency: `RetrievalEvaluationAgent`, `RetrievalEvaluationReport`, `RetrievalEvaluationCheck`, `RetrievalJudgement`, `retrieval_evaluation_status`, and `retrieval_quality_score` are named consistently.
- Safety: Unit tests mock LLM calls; real DeepSeek smoke is optional and explicitly budgeted.
