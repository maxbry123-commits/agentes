"""Strategy Memory — qué funcionó por task_type · 0% LLM
SOURCE: Fase 5 · alimenta selección de strategy
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StrategyRecord:
    task_type: str
    strategy: str
    model: str = ""
    agent: str = ""
    iterations: int = 0
    success: bool = False
    latency_seg: float = 0.0
    cost: float = 0.0
    quality: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)


class StrategyMemory:
    def __init__(self) -> None:
        self._records: list[StrategyRecord] = []

    def record(self, rec: StrategyRecord) -> None:
        self._records.append(rec)

    def best_for(self, task_type: str, limit: int = 5) -> list[StrategyRecord]:
        matched = [r for r in self._records if r.task_type == task_type and r.success]
        matched.sort(key=lambda r: (r.quality, -r.cost, -r.latency_seg), reverse=True)
        return matched[:limit]

    def suggest_strategy(self, task_type: str, default: str = "sequential") -> str:
        best = self.best_for(task_type, limit=1)
        return best[0].strategy if best else default

    def stats(self, task_type: str | None = None) -> dict[str, Any]:
        rows = self._records if task_type is None else [r for r in self._records if r.task_type == task_type]
        if not rows:
            return {"count": 0, "success_rate": 0.0}
        ok = sum(1 for r in rows if r.success)
        return {
            "count": len(rows),
            "success_rate": ok / len(rows),
            "strategies": list({r.strategy for r in rows}),
        }
