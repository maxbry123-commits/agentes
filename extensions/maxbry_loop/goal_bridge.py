"""T28 — sync GoalLock goals into per-instance loop state. No UI."""
from __future__ import annotations

from typing import Any

_LOOP_STATE: dict[str, dict[str, Any]] = {}


def loop_state(instance_id: str) -> dict[str, Any]:
    return _LOOP_STATE.setdefault(instance_id, {"instance_id": instance_id, "goals": None})


def sync_goals(instance_id: str, lock: dict[str, Any] | None = None) -> dict[str, Any]:
    state = loop_state(instance_id)
    if lock is None:
        lock = {
            "lock_id": f"GL-{instance_id}",
            "goals_in": {"text": f"goal:{instance_id}"},
            "source": "stub",
        }
    state["goals"] = lock
    state["goal_visible"] = True
    state["lock_id"] = lock.get("lock_id")
    return {"ok": True, "instance_id": instance_id, "goals": lock, "state": state}


if __name__ == "__main__":
    a = sync_goals("v1", {"lock_id": "GL-A", "goals_in": {"text": "A"}})
    b = sync_goals("v2", {"lock_id": "GL-B", "goals_in": {"text": "B"}})
    assert loop_state("v1")["goals"]["lock_id"] == "GL-A"
    assert loop_state("v2")["goals"]["lock_id"] == "GL-B"
    assert loop_state("v1")["goal_visible"] is True
    print("ok", a["ok"], loop_state("v1")["lock_id"], loop_state("v2")["lock_id"])
