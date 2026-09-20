"""Recovery Engine — 11 acciones · 0% LLM
SOURCE: PolicyDecision actions · F1-F16 reducido
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from loops.contracts.types import LoopContext, PolicyDecision

RECOVERY_ACTIONS = frozenset({
    "RETRY",
    "REPAIR",
    "REFRAME",
    "CHANGE_STRATEGY",
    "CHANGE_MODEL",
    "CHANGE_AGENT",
    "REDUCE_SCOPE",
    "ROLLBACK",
    "ISOLATE",
    "CHECKPOINT",
    "ESCALATE",
    "ABORT",
})


@dataclass
class RecoveryResult:
    ok: bool
    action_applied: str
    next_state: str
    ctx_updates: dict[str, Any] = field(default_factory=dict)
    message: str = ""
    escalate: bool = False


class RecoveryEngine:
    """Aplica decisión de policy a contexto + estado destino."""

    def apply(self, ctx: LoopContext, decision: PolicyDecision) -> RecoveryResult:
        action = decision.action
        repair_count = int((ctx.recovery_state or {}).get("repair_count") or 0)

        if action in ("CONTINUE", "CLOSE"):
            return RecoveryResult(
                ok=True,
                action_applied=action,
                next_state="RUNNING" if action == "CONTINUE" else "CLOSED",
                message=decision.reason,
            )

        if action == "HUMAN_GATE":
            return RecoveryResult(
                ok=True,
                action_applied=action,
                next_state="PAUSED",
                message=decision.reason or "awaiting human",
            )

        if action == "CHECKPOINT":
            return RecoveryResult(
                ok=True,
                action_applied=action,
                next_state="CHECKPOINT",
                message=decision.reason,
            )

        if action in ("REPAIR", "RETRY"):
            if repair_count >= int((ctx.budgets or {}).get("retry_budget") or 2):
                return RecoveryResult(
                    ok=False,
                    action_applied="ESCALATE",
                    next_state="ESCALATED",
                    escalate=True,
                    message="repair budget exhausted",
                    ctx_updates={"recovery_state": {"repair_count": repair_count}},
                )
            return RecoveryResult(
                ok=True,
                action_applied=action,
                next_state="REPAIRING" if action == "REPAIR" else "RUNNING",
                ctx_updates={
                    "recovery_state": {"repair_count": repair_count + 1},
                    "iteration": ctx.iteration,  # caller may bump
                },
                message=decision.reason,
            )

        if action == "CHANGE_STRATEGY":
            new_s = (decision.params or {}).get("new_strategy") or "adversarial"
            return RecoveryResult(
                ok=True,
                action_applied=action,
                next_state="RUNNING",
                ctx_updates={"strategy": new_s},
                message=f"strategy → {new_s}",
            )

        if action in ("CHANGE_MODEL", "CHANGE_AGENT", "REFRAME", "REDUCE_SCOPE", "ISOLATE"):
            return RecoveryResult(
                ok=True,
                action_applied=action,
                next_state="RUNNING",
                ctx_updates={"recovery_state": {**(ctx.recovery_state or {}), "last_action": action, **(decision.params or {})}},
                message=decision.reason,
            )

        if action == "ROLLBACK":
            return RecoveryResult(
                ok=True,
                action_applied=action,
                next_state="CHECKPOINT",
                message=decision.reason or "rollback to last checkpoint",
            )

        if action == "ESCALATE":
            return RecoveryResult(
                ok=False,
                action_applied=action,
                next_state="ESCALATED",
                escalate=True,
                message=decision.reason,
            )

        if action == "ABORT":
            return RecoveryResult(
                ok=False,
                action_applied=action,
                next_state="FAILED",
                message=decision.reason,
            )

        return RecoveryResult(
            ok=False,
            action_applied=action,
            next_state="FAILED",
            message=f"unknown recovery action: {action}",
        )
