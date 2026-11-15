# -*- coding: utf-8 -*-
"""ExpertPanel — T29. Structured multi-expert opinions. 0% LLM (stubs)."""
from __future__ import annotations

from typing import Any, Callable, Protocol


class Expert(Protocol):
    expert_id: str
    role: str

    def opine(self, topic: str, context: dict[str, Any]) -> dict[str, Any]: ...


class StaticExpert:
    """Deterministic stub expert."""

    def __init__(
        self,
        expert_id: str,
        role: str,
        *,
        vote: str = "APPROVE",
        confidence: float = 0.8,
        reasons: list[str] | None = None,
    ):
        self.expert_id = expert_id
        self.role = role
        self.vote = vote
        self.confidence = confidence
        self.reasons = list(reasons or [f"static:{role}"])

    def opine(self, topic: str, context: dict[str, Any]) -> dict[str, Any]:
        return {
            "expert_id": self.expert_id,
            "role": self.role,
            "vote": self.vote,
            "confidence": self.confidence,
            "reasons": list(self.reasons),
            "meta": {"topic": topic, "context_keys": list(context.keys())},
        }


class RuleExpert:
    """Votes REJECT if context flag risk_high else APPROVE."""

    def __init__(self, expert_id: str = "rule_risk", role: str = "risk"):
        self.expert_id = expert_id
        self.role = role

    def opine(self, topic: str, context: dict[str, Any]) -> dict[str, Any]:
        high = bool(context.get("risk_high") or context.get("risk_score", 0) >= 8)
        return {
            "expert_id": self.expert_id,
            "role": self.role,
            "vote": "REJECT" if high else "APPROVE",
            "confidence": 0.9 if high else 0.7,
            "reasons": ["risk_high" if high else "risk_ok"],
            "meta": {"topic": topic},
        }


class ExpertPanel:
    """Collect opinions; does not decide (YAIWES / DecisionGate does)."""

    def __init__(self, experts: list[Any] | None = None):
        self.experts: list[Any] = list(experts or [])

    def add(self, expert: Any) -> None:
        self.experts.append(expert)

    def collect(self, topic: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = dict(context or {})
        opinions = [e.opine(topic, ctx) for e in self.experts]
        tally: dict[str, int] = {}
        for o in opinions:
            tally[o["vote"]] = tally.get(o["vote"], 0) + 1
        return {
            "topic": topic,
            "opinions": opinions,
            "tally": tally,
            "n": len(opinions),
        }
