# -*- coding: utf-8 -*-
"""expert_router — T31. Select experts by task class. 0% LLM."""
from __future__ import annotations

from typing import Any

from .expert_decision import panel_decide
from .expert_panel import ExpertPanel, RuleExpert, StaticExpert

# Default roster per task class (stubs)
ROSTERS: dict[str, list[tuple[str, str]]] = {
    "DETERMINISTIC": [("det_arch", "architecture"), ("det_qa", "qa")],
    "SEARCH": [("search_lead", "research"), ("search_sec", "security")],
    "CODE": [("code_arch", "architecture"), ("code_sec", "security"), ("code_qa", "qa")],
    "REASONING": [("rsn_plan", "planning"), ("rsn_risk", "risk")],
    "DEFAULT": [("gen_a", "general"), ("gen_b", "general")],
}


def build_panel_for_class(
    task_class: str,
    *,
    include_rule_risk: bool = True,
) -> ExpertPanel:
    key = (task_class or "DEFAULT").upper()
    roster = ROSTERS.get(key) or ROSTERS["DEFAULT"]
    experts: list[Any] = [
        StaticExpert(eid, role, vote="APPROVE", confidence=0.75) for eid, role in roster
    ]
    if include_rule_risk:
        experts.append(RuleExpert())
    return ExpertPanel(experts)


def route_and_decide(
    topic: str,
    *,
    task_class: str = "DEFAULT",
    context: dict[str, Any] | None = None,
    include_rule_risk: bool = True,
    **decide_kwargs: Any,
) -> dict[str, Any]:
    panel = build_panel_for_class(task_class, include_rule_risk=include_rule_risk)
    result = panel_decide(panel, topic, context, **decide_kwargs)
    result["task_class"] = (task_class or "DEFAULT").upper()
    result["roster_size"] = result["panel"]["n"]
    return result
