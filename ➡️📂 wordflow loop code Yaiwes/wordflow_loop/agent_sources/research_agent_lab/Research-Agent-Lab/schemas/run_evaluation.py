from __future__ import annotations

from dataclasses import dataclass, field

from schemas.base import new_id, utc_now


@dataclass(slots=True)
class RunEvaluationCheck:
    name: str
    status: str
    severity: str
    message: str
    evidence: dict = field(default_factory=dict)


@dataclass(slots=True)
class RunEvaluationReport:
    status: str
    score: int
    recommended_next_action: str
    evaluation_id: str = field(default_factory=lambda: new_id("runeval"))
    created_at: str = field(default_factory=utc_now)
    checks: list[RunEvaluationCheck] = field(default_factory=list)
    blocking_issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    summary: list[str] = field(default_factory=list)
