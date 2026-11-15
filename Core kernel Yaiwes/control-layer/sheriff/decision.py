# -*- coding: utf-8 -*-
"""sheriff/decision.py — Sheriff Decision Engine 0% LLM.
Fuente: SALIDA 4 §20
Decide ALLOW / DENY / ESCALATE según estado + plan.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from control.compiler import CompilePlan
from control.threat import ThreatResult

from .states import SheriffState, can_transition, state_from_band


@dataclass(frozen=True)
class SheriffDecision:
    state: SheriffState
    action: str  # ALLOW | DENY | ESCALATE
    reason: str
    risk_score: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "action": self.action,
            "reason": self.reason,
            "risk_score": self.risk_score,
        }


def decide(
    plan: CompilePlan,
    current: Optional[SheriffState] = None,
) -> SheriffDecision:
    """Decisión determinista a partir del CompilePlan."""
    threat: ThreatResult = plan.threat
    target = state_from_band(threat.band, threat.risk_score)

    if not plan.ok:
        return SheriffDecision(
            state=SheriffState.RED,
            action="DENY",
            reason="plan.ok=false conflicts=" + ",".join(plan.conflicts),
            risk_score=threat.risk_score,
        )

    if current is not None and not can_transition(current, target):
        return SheriffDecision(
            state=current,
            action="DENY",
            reason=f"transicion_prohibida {current.value}->{target.value}",
            risk_score=threat.risk_score,
        )

    if target == SheriffState.RED:
        return SheriffDecision(
            state=target,
            action="DENY",
            reason="risk_quarantine",
            risk_score=threat.risk_score,
        )
    if target == SheriffState.BLACK:
        return SheriffDecision(
            state=target,
            action="DENY",
            reason="state_black",
            risk_score=threat.risk_score,
        )
    if target == SheriffState.ORANGE:
        return SheriffDecision(
            state=target,
            action="ESCALATE",
            reason="risk_elevated",
            risk_score=threat.risk_score,
        )
    if target == SheriffState.YELLOW:
        return SheriffDecision(
            state=target,
            action="ALLOW",
            reason="sheriff_check_pass",
            risk_score=threat.risk_score,
        )
    return SheriffDecision(
        state=SheriffState.GREEN,
        action="ALLOW",
        reason="normal",
        risk_score=threat.risk_score,
    )
