# -*- coding: utf-8 -*-
"""kimi_policy — D8. Deliberation budget + confidence gate. 0% LLM core.

LLM only when classifier allows REASONING/HYBRID and policy enables.
Default llm_control=DENY for core path.
"""
from __future__ import annotations

from typing import Any

BUDGETS = {
    "low": {"max_tokens_hint": 512, "allow_llm": False},
    "high": {"max_tokens_hint": 4096, "allow_llm": True},
    "max": {"max_tokens_hint": 16384, "allow_llm": True},
}


def deliberation_budget(level: str = "low") -> dict[str, Any]:
    key = (level or "low").lower()
    if key not in BUDGETS:
        return {"ok": False, "reason": "UNKNOWN_LEVEL", "known": list(BUDGETS)}
    b = dict(BUDGETS[key])
    return {"ok": True, "level": key, **b}


def confidence_gate(
    score: float,
    *,
    threshold: float = 0.55,
    require_evidence: bool = True,
    evidence_count: int = 0,
) -> dict[str, Any]:
    if score < 0 or score > 1:
        return {"ok": False, "reason": "SCORE_RANGE", "action": "DENY"}
    if require_evidence and evidence_count < 1 and score < 0.9:
        return {
            "ok": False,
            "reason": "EVIDENCE_REQUIRED",
            "action": "DENY",
            "score": score,
        }
    if score < threshold:
        return {
            "ok": False,
            "reason": "BELOW_THRESHOLD",
            "action": "DENY",
            "score": score,
            "threshold": threshold,
        }
    return {
        "ok": True,
        "action": "ALLOW",
        "score": score,
        "threshold": threshold,
    }


def may_invoke_llm(
    *,
    task_class: str,
    budget_level: str = "low",
    llm_control: str = "DENY",
) -> dict[str, Any]:
    """Pre-LLM gate: deterministic path preferred."""
    if (llm_control or "DENY").upper() == "DENY":
        return {"ok": False, "reason": "LLM_CONTROL_DENY", "invoke": False}
    tc = (task_class or "").upper()
    if tc in ("DETERMINISTIC", "SEARCH"):
        return {"ok": False, "reason": "CLASS_NO_LLM", "invoke": False, "task_class": tc}
    budget = deliberation_budget(budget_level)
    if not budget.get("ok") or not budget.get("allow_llm"):
        return {"ok": False, "reason": "BUDGET_BLOCKS_LLM", "budget": budget, "invoke": False}
    if tc not in ("REASONING", "HYBRID", "ANALYSIS"):
        return {"ok": False, "reason": "CLASS_UNKNOWN", "invoke": False}
    return {
        "ok": True,
        "invoke": True,
        "task_class": tc,
        "budget": budget,
        "note": "caller must still pass confidence_gate on output",
    }
