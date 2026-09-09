from dataclasses import dataclass
from typing import Literal

Stage = Literal["seed", "seed_repair", "nemotron", "deepseek", "done"]


@dataclass
class RepairState:
    task_id: str
    stage: Stage = "seed"
    attempts: int = 0
    last_error: str | None = None


class RepairLoop:
    """Política de reparación (SOURCE: arquitectura final de hf.md).

    Seed → TEST → FAIL → Seed repair #1 → TEST → FAIL → Nemotron →
    repair → TEST → FAIL → DeepSeek V4
    """

    MAX_SEED_REPAIRS = 1
    MAX_NEMOTRON = 1

    def next_stage(self, state: RepairState, test_passed: bool) -> RepairState:
        if test_passed:
            state.stage = "done"
            return state

        state.attempts += 1

        if state.stage == "seed":
            state.stage = "seed_repair"
            return state

        if state.stage == "seed_repair":
            state.stage = "nemotron"
            return state

        if state.stage == "nemotron":
            state.stage = "deepseek"
            return state

        # already at deepseek and still failing
        state.stage = "done"
        return state
