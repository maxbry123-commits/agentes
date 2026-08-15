# -*- coding: utf-8 -*-
"""C-17 repair_gate — enforce max_repair from Policy Engine. 0% LLM."""
from __future__ import annotations

from typing import Any

from .policy_engine import load_policy


class RepairGateError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


class RepairGate:
    def __init__(self, policy: dict[str, Any] | None = None):
        self.policy = policy or load_policy()
        self._attempts: dict[str, int] = {}

    @property
    def max_repair(self) -> int:
        limits = self.policy.get("limits") or {}
        return int(limits.get("max_repair", 2))

    def attempts(self, task_id: str) -> int:
        return self._attempts.get(task_id, 0)

    def can_repair(self, task_id: str) -> dict[str, Any]:
        n = self.attempts(task_id)
        allowed = n < self.max_repair
        return {
            "ok": allowed,
            "task_id": task_id,
            "attempts": n,
            "max_repair": self.max_repair,
            "reason_codes": [] if allowed else ["MAX_REPAIR_EXCEEDED"],
            "llm_control": "DENY",
        }

    def record_attempt(self, task_id: str, *, success: bool = False) -> dict[str, Any]:
        if not task_id:
            raise RepairGateError("TASK_ID_EMPTY")
        gate = self.can_repair(task_id)
        if not gate["ok"]:
            raise RepairGateError("MAX_REPAIR_EXCEEDED", task_id)
        self._attempts[task_id] = self.attempts(task_id) + 1
        return {
            "ok": True,
            "task_id": task_id,
            "attempts": self.attempts(task_id),
            "success": success,
            "llm_control": "DENY",
        }

    def reset(self, task_id: str) -> None:
        self._attempts.pop(task_id, None)
