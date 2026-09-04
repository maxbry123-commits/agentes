# -*- coding: utf-8 -*-
"""sheriff/gate.py — Sheriff Gate 0% LLM.
Fuente: SALIDA 4 §20 · CAPA_CONTROL_1
Checks base sobre CompilePlan + Decision antes de ejecutar.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

from control.compiler import CompilePlan

from .decision import SheriffDecision, decide
from .states import SheriffState


def load_policy(path: Optional[Path] = None) -> Dict[str, Any]:
    if path is None:
        path = Path(__file__).resolve().parents[1] / "policies" / "sheriff.yaml"
    if path.is_file() and yaml is not None:
        with path.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {
        "fail_closed": True,
        "checks": [
            {"id": "plan_ok", "required": True},
            {"id": "has_c00", "required": True},
            {"id": "no_conflicts", "required": True},
            {"id": "state_not_black", "required": True},
        ],
    }


@dataclass
class GateResult:
    passed: bool
    decision: SheriffDecision
    failed_checks: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "decision": self.decision.to_dict(),
            "failed_checks": list(self.failed_checks),
        }


def _run_checks(plan: CompilePlan, decision: SheriffDecision, policy: Dict[str, Any]) -> List[str]:
    failed: List[str] = []
    for chk in policy.get("checks", []):
        cid = chk.get("id", "")
        if cid == "plan_ok" and not plan.ok:
            failed.append("plan_ok")
        elif cid == "has_c00" and "C00" not in plan.contracts:
            failed.append("has_c00")
        elif cid == "no_conflicts" and plan.conflicts:
            failed.append("no_conflicts")
        elif cid == "state_not_black" and decision.state == SheriffState.BLACK:
            failed.append("state_not_black")
        elif cid == "risk_below_black":
            mx = int(chk.get("max_score", 10))
            if decision.risk_score > mx:
                failed.append("risk_below_black")
    return failed


def gate(
    plan: CompilePlan,
    current: Optional[SheriffState] = None,
    policy: Optional[Dict[str, Any]] = None,
) -> GateResult:
    """Evalúa plan → decisión → checks. Determinista."""
    pol = policy or load_policy()
    decision = decide(plan, current=current)
    failed = _run_checks(plan, decision, pol)

    if failed and pol.get("fail_closed", True):
        decision = SheriffDecision(
            state=SheriffState.RED,
            action="DENY",
            reason="gate_failed:" + ",".join(failed),
            risk_score=decision.risk_score,
        )
        return GateResult(passed=False, decision=decision, failed_checks=failed)

    if decision.action == "DENY":
        return GateResult(passed=False, decision=decision, failed_checks=failed)

    return GateResult(passed=True, decision=decision, failed_checks=failed)
