# -*- coding: utf-8 -*-
"""C-23 Blackboard — live operational state (not historical ledger). 0% LLM."""
from __future__ import annotations

import time
from typing import Any


class BlackboardError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


class Blackboard:
    """Mutable live board: goals, tasks, evidence, resources, blockers."""

    __slots__ = (
        "mission_id",
        "goals",
        "tasks",
        "evidence",
        "resources",
        "blockers",
        "metrics",
        "updated_at",
    )

    def __init__(self, mission_id: str = ""):
        self.mission_id = mission_id or ""
        self.goals: dict[str, Any] = {}
        self.tasks: dict[str, dict[str, Any]] = {}
        self.evidence: list[dict[str, Any]] = []
        self.resources: dict[str, dict[str, Any]] = {}
        self.blockers: dict[str, dict[str, Any]] = {}
        self.metrics: dict[str, Any] = {}
        self.updated_at = time.time()

    def _touch(self) -> None:
        self.updated_at = time.time()

    def set_goal(self, goal_id: str, payload: dict[str, Any]) -> None:
        if not goal_id:
            raise BlackboardError("GOAL_ID_EMPTY")
        self.goals[goal_id] = dict(payload)
        self._touch()

    def upsert_task(self, task_id: str, status: str, **fields: Any) -> None:
        if not task_id:
            raise BlackboardError("TASK_ID_EMPTY")
        row = self.tasks.get(task_id, {})
        row.update(fields)
        row["status"] = status
        row["task_id"] = task_id
        self.tasks[task_id] = row
        self._touch()

    def add_evidence(self, item: dict[str, Any]) -> None:
        if not isinstance(item, dict):
            raise BlackboardError("EVIDENCE_NOT_OBJECT")
        self.evidence.append(dict(item))
        self._touch()

    def set_resource(self, resource_id: str, state: str, **fields: Any) -> None:
        if not resource_id:
            raise BlackboardError("RESOURCE_ID_EMPTY")
        row = {"state": state, **fields}
        self.resources[resource_id] = row
        self._touch()

    def add_blocker(self, blocker_id: str, reason: str, **fields: Any) -> None:
        if not blocker_id:
            raise BlackboardError("BLOCKER_ID_EMPTY")
        self.blockers[blocker_id] = {"reason": reason, **fields}
        self._touch()

    def clear_blocker(self, blocker_id: str) -> None:
        self.blockers.pop(blocker_id, None)
        self._touch()

    def snapshot(self) -> dict[str, Any]:
        """Read-only live snapshot (not ledger history)."""
        return {
            "mission_id": self.mission_id,
            "goals": dict(self.goals),
            "tasks": {k: dict(v) for k, v in self.tasks.items()},
            "evidence": list(self.evidence),
            "resources": {k: dict(v) for k, v in self.resources.items()},
            "blockers": {k: dict(v) for k, v in self.blockers.items()},
            "metrics": dict(self.metrics),
            "updated_at": self.updated_at,
            "llm_control": "DENY",
        }

    def pending_tasks(self) -> list[str]:
        return [tid for tid, t in self.tasks.items() if t.get("status") == "PENDING"]

    def has_blockers(self) -> bool:
        return len(self.blockers) > 0
