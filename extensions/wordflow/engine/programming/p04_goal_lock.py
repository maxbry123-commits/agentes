# -*- coding: utf-8 -*-
"""Process 04 — Goal lock."""
from __future__ import annotations
from typing import Any


def run_goal_lock(raw_input: str, wire_trace: dict[str, Any]) -> dict[str, Any]:
    from extensions.wordflow.engine.goal_lock import lock_goals
    locked = lock_goals({"text": raw_input, "raw": raw_input})
    if not locked.get("ok"):
        return {"ok": False, "stage": "goal_lock", "detail": locked, "llm_control": "DENY", "verdict": "FAIL", "wire_trace": wire_trace}
    lock = locked.get("lock") or {}
    return {"ok": True, "lock": lock, "mission_id_hint": lock.get("lock_id") or ""}
