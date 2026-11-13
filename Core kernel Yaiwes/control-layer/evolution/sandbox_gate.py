"""EVO.09 · Sandbox → canary → registry."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class GateDecision(str, Enum):
    REJECT = "REJECT"
    SANDBOX_ONLY = "SANDBOX_ONLY"
    CANARY = "CANARY"
    PROMOTE = "PROMOTE"


@dataclass
class GateReport:
    decision: GateDecision
    tests_passed: bool
    security_ok: bool
    regression_ok: bool
    canary_ok: bool
    reasons: list[str] = field(default_factory=list)
    candidate_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["decision"] = self.decision.value
        return d


class SandboxGate:
    def evaluate(
        self,
        *,
        candidate_id: str,
        tests_passed: bool,
        security_ok: bool,
        regression_ok: bool,
        canary_ok: bool,
        trust_score: float = 0.0,
        min_trust: float = 0.7,
    ) -> GateReport:
        reasons: list[str] = []
        if not tests_passed:
            reasons.append("tests_failed")
        if not security_ok:
            reasons.append("security_failed")
        if not regression_ok:
            reasons.append("regression_failed")
        if trust_score < min_trust:
            reasons.append(f"trust_below_{min_trust}")
        if reasons:
            return GateReport(GateDecision.REJECT, tests_passed, security_ok, regression_ok, canary_ok, reasons, candidate_id)
        if not canary_ok:
            return GateReport(GateDecision.CANARY, True, True, True, False, ["await_canary"], candidate_id)
        return GateReport(GateDecision.PROMOTE, True, True, True, True, ["all_gates_pass"], candidate_id)
