# -*- coding: utf-8 -*-
"""mission — T26. Mission == GoalLock. Enforce before execute. 0% LLM."""
from __future__ import annotations

from typing import Any

from .goal_lock import verify_lock_integrity
from .loop_bridge import bridge_full, bridge_to_lock
from .sheriff_adapter import SheriffState, gate_lock


def mission_from_raw(raw_input: str, *,
                     full: bool = False) -> dict[str, Any]:
    """Create mission package. Mission identity = lock_id."""
    if full:
        pack = bridge_full(raw_input)
    else:
        pack = bridge_to_lock(raw_input, allow_raw_literal_fallback=True)
    if not pack.get("ok") and not pack.get("lock"):
        return {"ok": False, "stage": "mission_build", "detail": pack}
    lock = pack["lock"]
    return {
        "ok": True,
        "mission_id": lock.get("lock_id"),
        "lock": lock,
        "pack": pack,
    }


def enforce_mission(
    mission: dict[str, Any],
    *,
    risk_score: int = 0,
    band: str = "",
    current: SheriffState | None = None,
) -> dict[str, Any]:
    """Fail-closed: no execute if lock broken or Sheriff DENY."""
    lock = mission.get("lock") if isinstance(mission, dict) else None
    if not isinstance(lock, dict):
        return {"ok": False, "action": "DENY", "reason": "NO_LOCK"}

    integ = verify_lock_integrity(lock)
    if not integ.get("ok"):
        return {
            "ok": False,
            "action": "DENY",
            "reason": "MISSION_LOCK_TAMPER",
            "detail": integ,
        }

    mid = mission.get("mission_id") or lock.get("lock_id")
    if mid and lock.get("lock_id") and mid != lock.get("lock_id"):
        return {
            "ok": False,
            "action": "DENY",
            "reason": "MISSION_ID_MISMATCH",
        }

    g = gate_lock(lock, risk_score=risk_score, band=band, current=current)
    return {
        "ok": bool(g.get("passed")),
        "action": g.get("action"),
        "mission_id": lock.get("lock_id"),
        "sheriff": g,
    }


def require_mission(mission: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Alias enforce — raises nothing; returns DENY dict."""
    return enforce_mission(mission, **kwargs)
