"""Budget multi-task auto-reallocation · 0% LLM
SOURCE: P3 · pool compartido entre runs del mismo project/task
"""
from __future__ import annotations
from dataclasses import dataclass, field

from loops.budget_governor import BudgetGovernor, budget_from_level
from loops.contracts.types import BudgetLevel


@dataclass
class PoolMember:
    run_id: str
    governor: BudgetGovernor
    weight: float = 1.0


class BudgetPool:
    def __init__(self, level: BudgetLevel = "fase") -> None:
        self.level = level
        self.members: dict[str, PoolMember] = {}

    def add(self, run_id: str, governor: BudgetGovernor | None = None, weight: float = 1.0) -> BudgetGovernor:
        g = governor or BudgetGovernor(budget_from_level(self.level))
        self.members[run_id] = PoolMember(run_id=run_id, governor=g, weight=weight)
        return g

    def rebalance(self) -> dict[str, dict[str, float]]:
        """Redistribuye residual de runs closed/idle hacia activos."""
        moved: dict[str, dict[str, float]] = {}
        donors = []
        receivers = []
        for m in self.members.values():
            res = m.governor.residual()
            if res.get("tokens", 0) > 1000 and m.governor.budget.iterations_used == 0:
                donors.append(m)
            elif m.governor.budget.iterations_used > 0:
                receivers.append(m)
        if not donors or not receivers:
            return moved
        for d in donors:
            for r in receivers:
                got = r.governor.reallocate_from(d.governor, fraction=0.25 / max(len(receivers), 1))
                if got:
                    moved.setdefault(r.run_id, {}).update(got)
        return moved

    def snapshot(self) -> dict[str, dict]:
        return {rid: m.governor.snapshot() for rid, m in self.members.items()}
