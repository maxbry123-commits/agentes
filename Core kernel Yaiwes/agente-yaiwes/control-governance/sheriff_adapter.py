# -*- coding: utf-8 -*-
"""sheriff_adapter — T25. Wordflow bridge to Sheriff 5 estados. 0% LLM.

Does NOT rewrite control-layer/sheriff.
Canonical states live in control-layer/sheriff/states.py (GREEN…BLACK).
This module:
  1) Mirrors the 5 states for GoalLock path without CompilePlan dependency.
  2) Optionally imports control-layer symbols when package path allows.
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from .goal_lock import verify_lock_integrity


class SheriffState(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    ORANGE = "ORANGE"
    RED = "RED"
    BLACK = "BLACK"


ALLOWED: dict[SheriffState, set[SheriffState]] = {
    SheriffState.GREEN: {SheriffState.GREEN, SheriffState.YELLOW, SheriffState.ORANGE},
    SheriffState.YELLOW: {
        SheriffState.GREEN,
        SheriffState.YELLOW,
        SheriffState.ORANGE,
        SheriffState.RED,
    },
    SheriffState.ORANGE: {SheriffState.YELLOW, SheriffState.ORANGE, SheriffState.RED},
    SheriffState.RED: {SheriffState.ORANGE, SheriffState.RED, SheriffState.BLACK},
    SheriffState.BLACK: {SheriffState.BLACK},
}


def can_transition(src: SheriffState, dst: SheriffState) -> bool:
    return dst in ALLOWED.get(src, set())


def state_from_band(band: str, risk_score: int) -> SheriffState:
    b = (band or "").lower()
    if b == "quarantine" or risk_score >= 8:
        return SheriffState.RED
    if b in ("sheriff_check", "elevated") or risk_score >= 4:
        return SheriffState.YELLOW
    if risk_score >= 6:
        return SheriffState.ORANGE
    return SheriffState.GREEN


def gate_lock(
    lock: dict[str, Any],
    *,
    risk_score: int = 0,
    band: str = "",
    current: SheriffState | None = None,
    fail_closed: bool = True,
) -> dict[str, Any]:
    """Sheriff gate for Wordflow GoalLock path (no CompilePlan)."""
    integ = verify_lock_integrity(lock)
    if not integ.get("ok"):
        return {
            "passed": False,
            "action": "DENY",
            "state": SheriffState.RED.value,
            "reason": "LOCK_INTEGRITY_FAIL",
            "detail": integ,
        }

    state = state_from_band(band, int(risk_score))
    if current is not None and not can_transition(current, state):
        if fail_closed:
            return {
                "passed": False,
                "action": "DENY",
                "state": current.value,
                "reason": "INVALID_TRANSITION",
                "attempted": state.value,
            }

    if state == SheriffState.BLACK:
        return {
            "passed": False,
            "action": "DENY",
            "state": state.value,
            "reason": "STATE_BLACK",
        }
    if state == SheriffState.RED:
        return {
            "passed": False,
            "action": "DENY",
            "state": state.value,
            "reason": "STATE_RED",
            "risk_score": risk_score,
        }

    action = "ALLOW"
    if state in (SheriffState.YELLOW, SheriffState.ORANGE):
        action = "ALLOW_WITH_CONSTRAINTS"

    return {
        "passed": True,
        "action": action,
        "state": state.value,
        "reason": "OK",
        "risk_score": risk_score,
        "lock_id": lock.get("lock_id"),
        "source": "wordflow.sheriff_adapter",
        "control_layer": "control-layer/sheriff (states mirrored; full gate uses CompilePlan)",
    }


def try_import_control_sheriff() -> dict[str, Any]:
    """Probe control-layer sheriff package. Does not fail hard."""
    try:
        from control_layer.sheriff.states import SheriffState as CLState  # type: ignore

        return {"ok": True, "via": "control_layer.sheriff", "sample": CLState.GREEN.value}
    except Exception:
        pass
    try:
        # alternate path if control is top-level under control-layer on PYTHONPATH
        import importlib

        mod = importlib.import_module("sheriff.states")
        return {"ok": True, "via": "sheriff.states", "has": hasattr(mod, "SheriffState")}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": str(exc)}
