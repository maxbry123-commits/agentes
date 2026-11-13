from typing import Dict
from .models import Plan, LoopState, StepFn


class DeterministicLoopEngine:
    """12-stage execution loop. Kernel owns state and gates. No stage requires LLM."""

    STAGES = [
        "ADMIT",
        "LOCK_GOALS",
        "LOAD_CONTEXT",
        "AUDIT",
        "ACQUIRE",
        "PLAN",
        "EXECUTE",
        "VALIDATE",
        "REFUTE",
        "REPAIR",
        "VERIFY",
        "CLOSE",
    ]

    def __init__(self, handlers: Dict[str, StepFn], max_iterations: int = 3, max_repairs: int = 2):
        self.handlers = handlers
        self.max_iterations = max_iterations
        self.max_repairs = max_repairs

    def run(self, plan: Plan, state: LoopState | None = None) -> LoopState:
        state = state or LoopState(mission_id=plan.mission_id)
        if state.mission_id != plan.mission_id:
            raise ValueError("mission_id mismatch")

        while state.current_step < len(self.STAGES):
            if state.iteration >= self.max_iterations:
                state.status = "STOPPED_MAX_ITER"
                return state

            stage = self.STAGES[state.current_step]
            handler = self.handlers.get(stage)
            if handler is None:
                state.status = "STOPPED_MISSING_HANDLER"
                state.failed.append(stage)
                return state

            state.status = stage
            result = handler(plan, state)
            state.evidence[stage] = result.evidence

            if result.status == "PASS":
                state.completed.append(stage)
                state.current_step += 1
                continue

            if result.status == "REPLAN":
                state.iteration += 1
                state.current_step = 5  # PLAN
                continue

            if result.status == "REPAIR":
                if state.repair_count >= self.max_repairs:
                    state.status = "STOPPED_REPAIR_LIMIT"
                    state.failed.append(stage)
                    return state
                state.repair_count += 1
                state.current_step = 9  # REPAIR
                continue

            state.failed.append(stage)
            state.status = "STOPPED"
            return state

        state.status = "COMPLETED"
        return state
