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
            _save_judge_call_record(context, state, reason, reason, "", {})
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


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


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
    mix = Counter(str(p.get("source") or "unknown") for p in papers)
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
        if _safe_float(seed.get("relevance_score", 0.0)) < LOW_REFERENCE_SEED_SCORE
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
    routes = state.topic.metadata.get("models", {}).get("routes", {})
    if "retrieval_judge" not in routes:
        return router.route_for("paper_triage")
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
