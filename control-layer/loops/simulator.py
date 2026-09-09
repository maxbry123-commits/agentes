"""Loop Simulator + chaos scenarios · 0% LLM
SOURCE: P2 · pruebas sin modelos
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

from loops.contracts.types import DetectorResult, LoopContext
from loops.engine import LoopEngine, LoopRunResult
from loops.policy.engine import PolicyEngine


def _ctx(run_id: str = "R-sim", **kw: Any) -> LoopContext:
    base = dict(
        run_id=run_id, loop_id="L01", project_id="P", agent_id="A",
        task_id="T", goal_id="G", created_at="t", updated_at="t",
        budgets={"retry_budget": 2}, recovery_state={"repair_count": 0},
    )
    base.update(kw)
    return LoopContext(**base)


@dataclass
class SimResult:
    name: str
    ok: bool
    final_state: str
    iterations: int
    notes: str = ""


class LoopSimulator:
    def __init__(self, engine: LoopEngine | None = None) -> None:
        self.engine = engine or LoopEngine(policy=PolicyEngine([
            {"id": "close", "when": {"phase_outcome": "validation_passed", "goal_complete": True},
             "action": "CLOSE", "reason": "done"},
            {"id": "cont", "when": {"phase_outcome": "validation_passed", "goal_complete": False},
             "action": "CONTINUE", "reason": "go"},
        ]))

    def scenario_happy_close(self) -> SimResult:
        r = self.engine.run_iteration(_ctx(), goal_complete=True)
        return SimResult("happy_close", r.closed and r.ctx.state == "CLOSED", r.ctx.state, r.ctx.iteration)

    def scenario_stall_then_change(self) -> SimResult:
        ctx = _ctx()
        last = None
        for i in range(4):
            last = self.engine.run_iteration(
                ctx, goal_complete=False, progress_value=0.02, progress_kind="numeric"
            )
            ctx = last.ctx
            if ctx.state not in ("RUNNING", "REPAIRING", "CREATED", "LOCKED"):
                break
        assert last is not None
        return SimResult(
            "stall_path", True, last.ctx.state, last.ctx.iteration,
            notes=str(last.last_decision.action if last.last_decision else ""),
        )

    def scenario_budget_exhaust(self) -> SimResult:
        eng = LoopEngine(policy=PolicyEngine([]))
        # micro budget tiny
        from loops.budget_governor import BudgetGovernor, budget_from_level
        eng.budget = BudgetGovernor(budget_from_level("micro"))
        ctx = _ctx()
        last = None
        for _ in range(12):
            last = eng.run_iteration(ctx, goal_complete=False, charge_tokens=5000)
            ctx = last.ctx
            if last.closed:
                break
        assert last is not None
        return SimResult("budget_exhaust", True, last.ctx.state, last.ctx.iteration)

    def scenario_high_risk_pause(self) -> SimResult:
        r = self.engine.run_iteration(_ctx(), risk_actions=["delete"])
        return SimResult("high_risk_pause", r.ctx.state == "PAUSED", r.ctx.state, r.ctx.iteration)

    def run_all(self) -> list[SimResult]:
        return [
            self.scenario_happy_close(),
            self.scenario_stall_then_change(),
            self.scenario_budget_exhaust(),
            self.scenario_high_risk_pause(),
        ]


class ChaosMonkey:
    """Inyecta fallos controlados."""

    def drop_lease(self, supervisor: Any, run_id: str) -> None:
        supervisor.leases.release(run_id, supervisor.config.worker_id)

    def force_detector(self, detector: str = "timeout", severity: float = 0.9) -> list[DetectorResult]:
        from datetime import datetime, timezone
        return [DetectorResult(
            detector=detector,  # type: ignore[arg-type]
            severity=severity,
            fired_at=datetime.now(timezone.utc).isoformat(),
            run_id="chaos",
            action_hint="escalate",
        )]

    def duplicate_iteration(self, engine: LoopEngine, ctx: LoopContext) -> tuple[LoopRunResult, LoopRunResult]:
        ctx.idempotency_key = ctx.idempotency_key or "chaos-dup"
        r1 = engine.run_iteration(ctx, goal_complete=False)
        r2 = engine.run_iteration(r1.ctx, goal_complete=False)
        return r1, r2
