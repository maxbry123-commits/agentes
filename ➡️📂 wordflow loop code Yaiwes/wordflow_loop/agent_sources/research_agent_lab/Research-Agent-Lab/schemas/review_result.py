from __future__ import annotations

from dataclasses import dataclass, field

from schemas.base import new_id


@dataclass(slots=True)
class ReviewResult:
    status: str
    review_id: str = field(default_factory=lambda: new_id("review"))
    findings: list[str] = field(default_factory=list)
    required_actions: list[str] = field(default_factory=list)
    residual_risk: list[str] = field(default_factory=list)
