from __future__ import annotations

from dataclasses import dataclass, field

from schemas.base import new_id


@dataclass(slots=True)
class ExperimentPlan:
    name: str
    hypothesis: str
    experiment_id: str = field(default_factory=lambda: new_id("experiment"))
    baseline: str = ""
    modification: str = ""
    files_to_change: list[str] = field(default_factory=list)
    dataset: str = ""
    training_config: dict[str, object] = field(default_factory=dict)
    metrics: list[str] = field(default_factory=list)
    ablation_studies: list[str] = field(default_factory=list)
    acceptance_criteria: dict[str, object] = field(default_factory=dict)
    success_criteria: dict[str, object] = field(default_factory=dict)
    rollback_plan: str = ""
    commands: list[str] = field(default_factory=list)
