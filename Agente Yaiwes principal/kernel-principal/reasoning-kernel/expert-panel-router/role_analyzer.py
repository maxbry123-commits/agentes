# -*- coding: utf-8 -*-
"""C-12 Expert Role Analyzer — scan available motors → AvailableMotors. 0% LLM."""
from __future__ import annotations

from typing import Any

# Built-in registry of roles the Wordflow can request (not embedded engines).
DEFAULT_MOTORS: dict[str, dict[str, Any]] = {
    "architect": {"kind": "role", "cost": 1, "latency": "low", "api": None},
    "security": {"kind": "role", "cost": 1, "latency": "low", "api": None},
    "qa": {"kind": "role", "cost": 1, "latency": "low", "api": None},
    "planning": {"kind": "role", "cost": 1, "latency": "low", "api": None},
    "risk": {"kind": "role", "cost": 1, "latency": "low", "api": None},
    "research": {"kind": "role", "cost": 2, "latency": "mid", "api": None},
    "general": {"kind": "role", "cost": 1, "latency": "low", "api": None},
}

TASK_CLASS_ROLES: dict[str, list[str]] = {
    "DETERMINISTIC": ["architect", "qa"],
    "SEARCH": ["research", "security"],
    "CODE": ["architect", "security", "qa"],
    "REASONING": ["planning", "risk"],
    "DEFAULT": ["general", "qa"],
}


def analyze_available_motors(
    registered: dict[str, dict[str, Any]] | None = None,
    *,
    task_class: str = "DEFAULT",
) -> dict[str, Any]:
    """Produce AvailableMotors map from registered + defaults filtered by task_class."""
    base = dict(DEFAULT_MOTORS)
    if registered:
        for k, v in registered.items():
            if isinstance(v, dict):
                base[k] = {**base.get(k, {}), **v}

    key = (task_class or "DEFAULT").upper()
    wanted = TASK_CLASS_ROLES.get(key) or TASK_CLASS_ROLES["DEFAULT"]
    selected = {role: dict(base[role]) for role in wanted if role in base}

    return {
        "ok": True,
        "task_class": key,
        "available_motors": selected,
        "all_known": sorted(base.keys()),
        "selected_roles": list(selected.keys()),
        "llm_control": "DENY",
    }


def build_council_contract(
    *,
    topic: str,
    plan: list[Any],
    task_class: str = "DEFAULT",
    registered_motors: dict[str, dict[str, Any]] | None = None,
    risks: list[str] | None = None,
    mission_id: str = "",
    panel_tally: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Assemble CouncilContract for Mission Planner (C-21)."""
    if not plan:
        return {"ok": False, "reason_code": "PLAN_EMPTY"}

    motors = analyze_available_motors(registered_motors, task_class=task_class)
    return {
        "ok": True,
        "topic": topic,
        "mission_id": mission_id,
        "plan": list(plan),
        "roles": motors["selected_roles"],
        "available_motors": motors["available_motors"],
        "risks": list(risks or []),
        "task_class": motors["task_class"],
        "panel_tally": dict(panel_tally or {}),
        "policies": {},
        "llm_control": "DENY",
    }
