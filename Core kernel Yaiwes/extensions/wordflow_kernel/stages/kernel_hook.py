from .models import Goal, Plan, LoopState
from .engine import DeterministicLoopEngine


class KernelLoopHook:
    """Activation hook: goals + plan → 12-stage loop."""

    def __init__(self, engine: DeterministicLoopEngine):
        self.engine = engine

    def activate(
        self,
        mission_id: str,
        goals: list[Goal],
        planned_steps: list[str],
        metadata=None,
    ) -> LoopState:
        if not goals:
            raise ValueError("No goals supplied")
        if not planned_steps:
            raise ValueError("No plan supplied")
        plan = Plan(
            mission_id=mission_id,
            goals=goals,
            steps=planned_steps,
            metadata=metadata or {},
        )
        return self.engine.run(plan)
