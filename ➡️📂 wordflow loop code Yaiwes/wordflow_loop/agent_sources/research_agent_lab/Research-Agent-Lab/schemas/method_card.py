from __future__ import annotations

from dataclasses import dataclass, field

from schemas.base import new_id


@dataclass(slots=True)
class MethodCard:
    paper_id: str
    task: str
    method_card_id: str = field(default_factory=lambda: new_id("method"))
    problem_setting: str = ""
    input_modalities: list[str] = field(default_factory=list)
    output: str = ""
    model_architecture: dict[str, str] = field(default_factory=dict)
    temporal_modeling: str = ""
    fusion_strategy: dict[str, str] = field(default_factory=dict)
    training_objective: str = ""
    datasets: list[str] = field(default_factory=list)
    metrics: list[str] = field(default_factory=list)
    main_results: str = ""
    limitations: list[str] = field(default_factory=list)
    reusable_ideas_for_current_topic: list[str] = field(default_factory=list)
    implementation_difficulty: str = "medium"
    risk: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
