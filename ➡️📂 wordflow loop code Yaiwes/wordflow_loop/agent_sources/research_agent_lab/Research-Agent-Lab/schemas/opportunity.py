from __future__ import annotations

from dataclasses import dataclass, field

from schemas.base import new_id


@dataclass(slots=True)
class ResearchOpportunity:
    title: str
    hypothesis: str
    opportunity_id: str = field(default_factory=lambda: new_id("opportunity"))
    based_on_papers: list[str] = field(default_factory=list)
    technical_strategy: str = ""
    expected_benefit: str = ""
    novelty_level: str = "medium"
    implementation_difficulty: str = "medium"
    data_requirement: str = ""
    risk: list[str] = field(default_factory=list)
    recommended_priority: int = 1
