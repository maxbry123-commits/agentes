"""Risk Engine + Human Gate · 0% LLM
SOURCE: arquitectura loops · policy HUMAN_GATE
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Literal

RiskLevel = Literal["low", "medium", "high"]

# Acción → riesgo base (extensible)
ACTION_RISK: dict[str, RiskLevel] = {
    "read": "low",
    "search": "low",
    "plan": "low",
    "validate": "low",
    "write_code": "medium",
    "edit_file": "medium",
    "run_tests": "medium",
    "delete": "high",
    "deploy": "high",
    "external_api": "high",
    "production_write": "high",
    "irreversible": "high",
}


@dataclass
class RiskAssessment:
    level: RiskLevel
    score: float  # 0-1
    reasons: list[str] = field(default_factory=list)
    require_human: bool = False


class RiskEngine:
    def __init__(self, overrides: dict[str, RiskLevel] | None = None):
        self.table = {**ACTION_RISK, **(overrides or {})}

    def assess(self, actions: list[str], *, context_flags: dict[str, bool] | None = None) -> RiskAssessment:
        flags = context_flags or {}
        levels: list[RiskLevel] = []
        reasons: list[str] = []
        for a in actions:
            lvl = self.table.get(a, "medium")
            levels.append(lvl)
            reasons.append(f"{a}={lvl}")
        if flags.get("production"):
            levels.append("high")
            reasons.append("production=true")
        if flags.get("irreversible"):
            levels.append("high")
            reasons.append("irreversible=true")

        if "high" in levels:
            level: RiskLevel = "high"
            score = 0.9
        elif "medium" in levels:
            level = "medium"
            score = 0.5
        else:
            level = "low"
            score = 0.15

        return RiskAssessment(
            level=level,
            score=score,
            reasons=reasons,
            require_human=(level == "high"),
        )


GateMode = Literal["AUTO", "SUPERVISED", "HUMAN_APPROVAL"]


@dataclass
class GateDecision:
    mode: GateMode
    allow: bool
    pause: bool
    reason: str


class HumanGate:
    """AUTO / SUPERVISED / HUMAN_APPROVAL según riesgo."""

    def decide(self, risk: RiskAssessment, *, supervised_force: bool = False) -> GateDecision:
        if risk.level == "high" or risk.require_human:
            return GateDecision(
                mode="HUMAN_APPROVAL",
                allow=False,
                pause=True,
                reason="high risk → HUMAN_GATE",
            )
        if risk.level == "medium" or supervised_force:
            return GateDecision(
                mode="SUPERVISED",
                allow=True,
                pause=False,
                reason="medium risk → supervised",
            )
        return GateDecision(
            mode="AUTO",
            allow=True,
            pause=False,
            reason="low risk → auto",
        )
