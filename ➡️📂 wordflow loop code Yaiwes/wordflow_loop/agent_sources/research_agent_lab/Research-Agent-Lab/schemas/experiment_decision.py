from __future__ import annotations

from dataclasses import dataclass, field

from schemas.base import new_id


@dataclass(slots=True)
class ExperimentDecision:
    experiment_id: str
    decision_id: str = field(default_factory=lambda: new_id("decision"))
    action: str = "hold"
    reason: str = ""
    based_on_result_ids: list[str] = field(default_factory=list)
    suggestion: str = ""
    requires_human_approval: bool = True
    notes: list[str] = field(default_factory=list)
