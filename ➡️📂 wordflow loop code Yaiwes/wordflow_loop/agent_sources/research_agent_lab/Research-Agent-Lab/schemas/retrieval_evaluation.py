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
