# -*- coding: utf-8 -*-
"""C-25 Context Builder — minimal payload before WF.MAIN_12. 0% LLM."""
from __future__ import annotations

import hashlib
import json
from typing import Any


class ContextError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def _slice_blackboard(bb: Any) -> dict[str, Any]:
    if bb is None:
        return {}
    if hasattr(bb, "snapshot") and callable(bb.snapshot):
        snap = bb.snapshot()
        return {"mission_id": snap.get("mission_id", ""), "tasks": snap.get("tasks", {}), "blockers": snap.get("blockers", {}), "resources": snap.get("resources", {})}
    if isinstance(bb, dict):
        return {"mission_id": bb.get("mission_id", ""), "tasks": bb.get("tasks", {}), "blockers": bb.get("blockers", {}), "resources": bb.get("resources", {})}
    raise ContextError("BLACKBOARD_INVALID", type(bb).__name__)


def build_context(*, mission: dict[str, Any] | None = None, goal_lock: dict[str, Any] | None = None, evidence: list[dict[str, Any]] | None = None, policies: dict[str, Any] | None = None, blackboard: Any = None, resources: dict[str, Any] | None = None) -> dict[str, Any]:
    if not mission and not goal_lock:
        raise ContextError("NO_MISSION_OR_LOCK")
    lock = goal_lock or (mission or {}).get("lock") or {}
    mission_id = (mission or {}).get("mission_id") or (lock or {}).get("lock_id") or ""
    packet = {"mission_id": mission_id, "mission": dict(mission) if isinstance(mission, dict) else {}, "goal_lock": dict(lock) if isinstance(lock, dict) else {}, "evidence": list(evidence or []), "policies": dict(policies or {}), "blackboard_slice": _slice_blackboard(blackboard), "resources": dict(resources or {}), "llm_control": "DENY"}
    canonical = json.dumps(packet, sort_keys=True, separators=(",", ":"), default=str)
    packet["context_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {"ok": True, "context": packet}
