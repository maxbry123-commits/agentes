from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


ALLOWED_LLM_REASONS = {
    "ambiguity_resolution",
    "semantic_ranking",
    "bounded_summary",
}


@dataclass(frozen=True)
class LLMBudget:
    deterministic_units: int
    llm_units: int = 0
    max_ratio: float = 0.05

    @property
    def ratio(self) -> float:
        total = self.deterministic_units + self.llm_units
        return 0.0 if total <= 0 else self.llm_units / total

    def allows(self, additional_llm_units: int = 1) -> bool:
        if additional_llm_units < 0:
            return False
        total = self.deterministic_units + self.llm_units + additional_llm_units
        if total <= 0:
            return False
        return (self.llm_units + additional_llm_units) / total <= self.max_ratio


class LLMGate:
    """LLM is optional, injected, and capped at 5% of declared work units."""

    def call(
        self,
        *,
        reason: str,
        prompt: str,
        caller: Callable[[str], Any] | None,
        budget: LLMBudget,
        units: int = 1,
    ) -> Any:
        if reason not in ALLOWED_LLM_REASONS:
            raise PermissionError(f"LLM reason not allowed: {reason}")
        if caller is None:
            raise RuntimeError("LLM caller is not connected")
        if not budget.allows(units):
            raise PermissionError("LLM budget would exceed 5%")
        return caller(prompt)
