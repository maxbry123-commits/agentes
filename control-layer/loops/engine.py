"""Loop Engine mínimo — orquesta SM + phases + policy + recovery + plugins.
SOURCE: contratos v1 · 0% LLM en control flow
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loops.contracts.types import (
    DetectorResult,
    LoopContext,
    LoopEvent,
    PolicyDecision,
)
from loops.phases import PhaseRunner, PhaseResult
from loops.plugins.base import GraphPlugin, MemoryPlugin, NoOpGraphPlugin, NoOpMemoryPlugin
from loops.policy.engine import PolicyEngine, PolicyInput
from loops.recovery import RecoveryEngine, RecoveryResult
from loops.state_machine import StateMachine


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class LoopRunResult:
    ctx: LoopContext
    events: list[LoopEvent] = field(default_factory=list)
    phase_results: list[PhaseResult] = field(default_factory=list)
    last_decision: PolicyDecision | None = None
    recovery: RecoveryResult | None = None
    closed: bool = False


class LoopEngine:
    def __init__(
        self,
        *,
        policy: PolicyEngine | None = None,
        memory: MemoryPlugin | None = None,
        graph: GraphPlugin | None = None,
        phase_handlers: dict | None = None,
    ):
        self.sm = StateMachine()
        self.phases = PhaseRunner(handlers=phase_handlers)
        self.policy = policy or PolicyEngine()
        self.recovery = RecoveryEngine()
        self.memory = memory or NoOpMemoryPlugin()
        self.graph = graph or NoOpGraphPlugin()

    @classmethod
    def with_default_policy(cls, policy_yaml: str | Path | None = None, **kwargs: Any) -> "LoopEngine":
        if policy_yaml is None:
            policy_yaml = Path(__file__).parent / "policy" / "default_policy.yaml"
        try:
            pol = PolicyEngine.from_yaml(policy_yaml)
        except Exception:
            pol = PolicyEngine()
        return cls(policy=pol, **kwargs)

    def _emit(self, ev: LoopEvent) -> None:
        self.memory.append_event(ev)
        self.graph.on_event(ev)

    def start(self, ctx: LoopContext) -> tuple[LoopContext, list[LoopEvent]]:
        events: list[LoopEvent] = []
        if ctx.state == "CREATED":
            ctx, ev = self.sm.transition(ctx, "LOCKED", event_type="LOOP_LOCKED")
            events.append(ev)
            self._emit(ev)
            ctx, ev = self.sm.transition(ctx, "RUNNING", event_type="PHASE_STARTED")
            events.append(ev)
            self._emit(ev)
        return ctx, events

    def run_iteration(
        self,
        ctx: LoopContext,
        *,
        detectors: list[DetectorResult] | None = None,
        goal_complete: bool = False,
        risk_level: str = "low",
    ) -> LoopRunResult:
        """Una iteración: phases → policy → recovery → state transition."""
        events: list[LoopEvent] = []
        if ctx.state == "CREATED":
            ctx, evs = self.start(ctx)
            events.extend(evs)

        if ctx.state not in ("RUNNING", "REPAIRING"):
            return LoopRunResult(ctx=ctx, events=events, closed=ctx.state in ("CLOSED", "FAILED", "ESCALATED", "CANCELLED"))

        # phases
        if ctx.state == "REPAIRING":
            ctx, ev = self.sm.transition(ctx, "RUNNING", event_type="REPAIR_COMPLETED")
            events.append(ev)
            self._emit(ev)

        phase_results, sheriff = self.phases.run({"run_id": ctx.run_id, "iteration": ctx.iteration})
        ctx, ev = self.sm.transition(ctx, "VALIDATING", event_type="PHASE_COMPLETED", payload={"sheriff_ok": sheriff.ok})
        events.append(ev)
        self._emit(ev)

        phase_outcome = "validation_passed" if sheriff.ok else "validation_failed"
        dets = list(detectors or [])
        if not sheriff.ok:
            dets.append(DetectorResult(
                detector="contract_violation",
                severity=0.95,
                fired_at=_now(),
                run_id=ctx.run_id,
                evidence=[sheriff.reason],
                action_hint="repair",
            ))

        # policy
        repair_count = int((ctx.recovery_state or {}).get("repair_count") or 0)
        decision = self.policy.evaluate(PolicyInput(
            run_id=ctx.run_id,
            iteration=ctx.iteration,
            repair_count=repair_count,
            phase_outcome=phase_outcome,
            goal_complete=goal_complete and sheriff.ok,
            risk_level=risk_level,
            detectors=dets,
        ))
        ctx, ev = self.sm.transition(ctx, "DECIDING", event_type="POLICY_DECIDED", payload={"action": decision.action})
        events.append(ev)
        self._emit(ev)

        # recovery
        rec = self.recovery.apply(ctx, decision)
        for k, v in (rec.ctx_updates or {}).items():
            if k == "recovery_state" and isinstance(v, dict):
                ctx.recovery_state = {**(ctx.recovery_state or {}), **v}
            elif k == "strategy":
                ctx.strategy = str(v)
            elif hasattr(ctx, k):
                setattr(ctx, k, v)

        target = rec.next_state
        # map decision events
        etype = {
            "CLOSED": "LOOP_COMPLETED",
            "ESCALATED": "LOOP_ESCALATED",
            "FAILED": "LOOP_FAILED",
            "PAUSED": "LOOP_PAUSED",
            "CHECKPOINT": "CHECKPOINT_CREATED",
            "REPAIRING": "REPAIR_STARTED",
            "RUNNING": "LOOP_CONTINUED",
        }.get(target, "DECISION_MADE")

        # ensure legal transition from DECIDING
        from loops.contracts.types import can_transition
        if not can_transition(ctx.state, target):
            # force via known path
            if target == "RUNNING":
                target = "RUNNING"
            elif target not in ("CLOSED", "ESCALATED", "FAILED", "CANCELLED", "PAUSED", "CHECKPOINT", "REPAIRING"):
                target = "FAILED"
                etype = "LOOP_FAILED"

        ctx, ev = self.sm.transition(ctx, target, event_type=etype, payload={"action": rec.action_applied})
        events.append(ev)
        self._emit(ev)

        if target == "RUNNING":
            ctx.iteration += 1

        closed = target in ("CLOSED", "FAILED", "ESCALATED", "CANCELLED")
        return LoopRunResult(
            ctx=ctx,
            events=events,
            phase_results=phase_results,
            last_decision=decision,
            recovery=rec,
            closed=closed,
        )
