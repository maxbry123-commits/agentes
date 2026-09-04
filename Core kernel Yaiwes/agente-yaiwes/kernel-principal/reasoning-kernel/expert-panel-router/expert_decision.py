# -*- coding: utf-8 -*-
"""expert_decision — T30. YAIWES DecisionGate over ExpertPanel tally. 0% LLM."""
from __future__ import annotations

from typing import Any

from .expert_panel import ExpertPanel


def decide_from_panel(
    panel_result: dict[str, Any],
    *,
    min_approve: int | None = None,
    reject_wins: bool = True,
    require_majority: bool = True,
) -> dict[str, Any]:
    """Deterministic decision from collect() output.

    Rules:
      1. If any REJECT and reject_wins → DENY
      2. Else if require_majority: APPROVE count > n/2 → ALLOW
      3. Else if min_approve set: APPROVE >= min_approve → ALLOW
      4. Else DENY (fail-closed)
    """
    opinions = list(panel_result.get("opinions") or [])
    tally = dict(panel_result.get("tally") or {})
    n = int(panel_result.get("n") or len(opinions))
    approve = int(tally.get("APPROVE", 0))
    reject = int(tally.get("REJECT", 0))
    abstain = int(tally.get("ABSTAIN", 0))
    revise = int(tally.get("REVISE", 0))

    if n == 0:
        return {
            "ok": False,
            "decision": "DENY",
            "reason": "NO_OPINIONS",
            "tally": tally,
        }

    if reject_wins and reject > 0:
        return {
            "ok": False,
            "decision": "DENY",
            "reason": "REJECT_PRESENT",
            "tally": tally,
            "decider": "YAIWES",
        }

    if revise > approve and revise > 0:
        return {
            "ok": False,
            "decision": "REVISE",
            "reason": "REVISE_DOMINANT",
            "tally": tally,
            "decider": "YAIWES",
        }

    if min_approve is not None:
        if approve >= min_approve:
            return {
                "ok": True,
                "decision": "ALLOW",
                "reason": "MIN_APPROVE",
                "tally": tally,
                "decider": "YAIWES",
            }
        return {
            "ok": False,
            "decision": "DENY",
            "reason": "BELOW_MIN_APPROVE",
            "tally": tally,
            "decider": "YAIWES",
        }

    if require_majority:
        if approve > n / 2:
            return {
                "ok": True,
                "decision": "ALLOW",
                "reason": "MAJORITY_APPROVE",
                "tally": tally,
                "decider": "YAIWES",
            }
        return {
            "ok": False,
            "decision": "DENY",
            "reason": "NO_MAJORITY",
            "tally": tally,
            "abstain": abstain,
            "decider": "YAIWES",
        }

    return {
        "ok": False,
        "decision": "DENY",
        "reason": "FAIL_CLOSED",
        "tally": tally,
        "decider": "YAIWES",
    }


def panel_decide(
    panel: ExpertPanel,
    topic: str,
    context: dict[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    collected = panel.collect(topic, context)
    decision = decide_from_panel(collected, **kwargs)
    return {"panel": collected, **decision}
