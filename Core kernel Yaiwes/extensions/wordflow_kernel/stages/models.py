from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List


@dataclass(frozen=True)
class Goal:
    id: str
    description: str
    required: bool = True


@dataclass
class Plan:
    mission_id: str
    goals: List[Goal]
    steps: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoopState:
    mission_id: str
    current_step: int = 0
    status: str = "READY"
    completed: List[str] = field(default_factory=list)
    failed: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    iteration: int = 0
    repair_count: int = 0


@dataclass
class StepResult:
    status: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""


StepFn = Callable[[Plan, LoopState], StepResult]
