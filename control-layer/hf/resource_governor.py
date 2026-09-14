from dataclasses import dataclass
from typing import Literal

Action = Literal["ALLOW", "LIMIT", "QUEUE", "UNLOAD", "EMERGENCY"]


@dataclass(frozen=True)
class GovernorDecision:
    action: Action
    max_concurrency: int
    reason: str


class ResourceGovernor:
    """Controla RAM/concurrencia por HF (SOURCE: arquitectura final de hf.md).

    Umbrales:
    <70%  → ALLOW
    70-85% → LIMIT
    85-92% → QUEUE / no cargar modelo extra
    92-95% → UNLOAD auxiliares
    >95%  → EMERGENCY
    """

    def evaluate(self, ram_percent: float, current_concurrency: int = 1) -> GovernorDecision:
        if ram_percent < 70:
            return GovernorDecision("ALLOW", max_concurrency=4, reason="RAM normal")
        if ram_percent < 85:
            return GovernorDecision("LIMIT", max_concurrency=2, reason="RAM alta")
        if ram_percent < 92:
            return GovernorDecision("QUEUE", max_concurrency=1, reason="RAM crítica — no cargar extra")
        if ram_percent < 95:
            return GovernorDecision("UNLOAD", max_concurrency=1, reason="UNLOAD auxiliares")
        return GovernorDecision("EMERGENCY", max_concurrency=0, reason="RAM emergencia")
