"""Budget Governor — consume · warn 80% · exhaust · reallocate residual · 0% LLM
SOURCE: budget.schema · LEVEL_DEFAULTS
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from loops.contracts.types import Budget, BudgetLevel, LEVEL_DEFAULTS, DetectorResult
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def budget_from_level(level: BudgetLevel = "tarea") -> Budget:
    d = LEVEL_DEFAULTS.get(level) or LEVEL_DEFAULTS["tarea"]
    return Budget(
        level=level,
        token_budget=int(d["tokens"]),
        time_budget_seg=int(d["time_seg"]),
        iteration_budget=int(d["max_iter"]),
        model_call_budget=int(d.get("model_calls") or 0),
        tool_call_budget=int(d.get("tool_calls") or 0),
    )


@dataclass
class BudgetReport:
    ok: bool
    warnings: list[str] = field(default_factory=list)
    exhausted: list[str] = field(default_factory=list)
    detectors: list[DetectorResult] = field(default_factory=list)


class BudgetGovernor:
    def __init__(self, budget: Budget | None = None, level: BudgetLevel = "tarea"):
        self.budget = budget or budget_from_level(level)

    def charge(
        self,
        *,
        tokens: int = 0,
        time_seg: float = 0,
        iteration: int = 0,
        tool_calls: int = 0,
        model_calls: int = 0,
        cost: float = 0,
        retries: int = 0,
        run_id: str = "",
    ) -> BudgetReport:
        b = self.budget
        b.tokens_used += tokens
        b.time_used_seg += time_seg
        b.iterations_used += iteration
        b.tool_calls_used += tool_calls
        b.model_calls_used += model_calls
        b.cost_used += cost
        b.retries_used += retries

        exhausted = b.exhausted()
        warnings = b.warning_80()
        detectors: list[DetectorResult] = []
        if exhausted:
            detectors.append(DetectorResult(
                detector="budget",
                severity=0.95,
                fired_at=_now(),
                run_id=run_id,
                evidence=exhausted,
                action_hint="escalate",
            ))
            detectors.append(DetectorResult(
                detector="resource_exhaustion",
                severity=0.9,
                fired_at=_now(),
                run_id=run_id,
                evidence=exhausted,
                action_hint="escalate",
            ))
        elif warnings:
            detectors.append(DetectorResult(
                detector="budget",
                severity=0.5,
                fired_at=_now(),
                run_id=run_id,
                evidence=warnings,
                action_hint="log",
            ))
        return BudgetReport(
            ok=len(exhausted) == 0,
            warnings=warnings,
            exhausted=exhausted,
            detectors=detectors,
        )

    def residual(self) -> dict[str, float]:
        b = self.budget
        return {
            "tokens": max(0, b.token_budget - b.tokens_used),
            "time_seg": max(0.0, b.time_budget_seg - b.time_used_seg),
            "iterations": max(0, b.iteration_budget - b.iterations_used),
        }

    def reallocate_from(self, other: "BudgetGovernor", fraction: float = 0.5) -> dict[str, float]:
        """Mueve fracción del residual de other hacia self (sibling runs)."""
        frac = max(0.0, min(1.0, fraction))
        moved: dict[str, float] = {}
        o, s = other.budget, self.budget
        tok = int((o.token_budget - o.tokens_used) * frac)
        if tok > 0:
            o.token_budget -= tok
            s.token_budget += tok
            moved["tokens"] = tok
        it = int((o.iteration_budget - o.iterations_used) * frac)
        if it > 0:
            o.iteration_budget -= it
            s.iteration_budget += it
            moved["iterations"] = it
        return moved

    def snapshot(self) -> dict[str, Any]:
        b = self.budget
        return {
            "level": b.level,
            "token_budget": b.token_budget,
            "tokens_used": b.tokens_used,
            "iteration_budget": b.iteration_budget,
            "iterations_used": b.iterations_used,
            "exhausted": b.exhausted(),
            "warnings": b.warning_80(),
        }
