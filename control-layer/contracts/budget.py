"""W04 · ChainBudget + Priority · límite de cadena completa."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class ChainBudget:
    max_tokens: int = 200_000
    max_cost_usd: float = 5.0
    max_seconds: int = 86_400  # 24h default long loop
    max_agent_calls: int = 50
    max_repairs: int = 10
    max_research: int = 30
    max_parallel: int = 5
    used_tokens: int = 0
    used_cost_usd: float = 0.0
    used_seconds: float = 0.0
    used_agent_calls: int = 0
    used_repairs: int = 0
    used_research: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def consume(
        self,
        *,
        tokens: int = 0,
        cost: float = 0.0,
        seconds: float = 0.0,
        agent_calls: int = 0,
        repairs: int = 0,
        research: int = 0,
    ) -> None:
        self.used_tokens += tokens
        self.used_cost_usd += cost
        self.used_seconds += seconds
        self.used_agent_calls += agent_calls
        self.used_repairs += repairs
        self.used_research += research

    def exhausted(self) -> list[str]:
        reasons: list[str] = []
        if self.used_tokens >= self.max_tokens:
            reasons.append("tokens")
        if self.used_cost_usd >= self.max_cost_usd:
            reasons.append("cost")
        if self.used_seconds >= self.max_seconds:
            reasons.append("time")
        if self.used_agent_calls >= self.max_agent_calls:
            reasons.append("agent_calls")
        if self.used_repairs >= self.max_repairs:
            reasons.append("repairs")
        if self.used_research >= self.max_research:
            reasons.append("research")
        return reasons

    def allow(self) -> bool:
        return len(self.exhausted()) == 0
