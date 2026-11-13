# -*- coding: utf-8 -*-
"""SandboxManager — T16. Logical slots only. 0% LLM."""
from __future__ import annotations

import uuid
from typing import Any


class SandboxError(Exception):
    pass


class SandboxManager:
    """Pool of logical sandboxes. No Docker/SSH in WAVE-3 base."""

    def __init__(self, n_slots: int = 1, *,
                 backend: str = "logical"):
        if n_slots < 1:
            raise ValueError("n_slots >= 1")
        if backend not in ("logical", "docker", "ssh", "other"):
            raise ValueError(f"invalid backend={backend}")
        if backend != "logical":
            # Allow registering future backends but only logical runs now
            pass
        self.backend = backend
        self._slots: dict[str, dict[str, Any]] = {}
        for _ in range(n_slots):
            sid = f"sb_{uuid.uuid4().hex[:10]}"
            self._slots[sid] = {
                "sandbox_id": sid,
                "status": "FREE",
                "backend": "logical",  # force logical until post-wire
                "task_id": None,
                "workdir": None,
                "lease_id": None,
            }

    def list_free(self) -> list[str]:
        return [s["sandbox_id"] for s in self._slots.values() if s["status"] == "FREE"]

    def list_all(self) -> list[dict[str, Any]]:
        return [dict(s) for s in self._slots.values()]

    def allocate(
        self,
        task_id: str,
        *,
        workdir: str | None = None,
        lease_id: str | None = None,
    ) -> dict[str, Any]:
        if not task_id:
            raise SandboxError("task_id required")
        free_id = next(
            (sid for sid, s in self._slots.items() if s["status"] == "FREE"),
            None,
        )
        if free_id is None:
            raise SandboxError("NO_FREE_SANDBOX")
        s = self._slots[free_id]
        s["status"] = "ALLOCATED"
        s["task_id"] = task_id
        s["workdir"] = workdir or f"/tmp/wordflow/{task_id}"
        s["lease_id"] = lease_id
        return dict(s)

    def mark_running(self, sandbox_id: str) -> dict[str, Any]:
        s = self._require(sandbox_id)
        if s["status"] not in ("ALLOCATED", "RUNNING"):
            raise SandboxError(f"cannot run from status={s['status']}")
        s["status"] = "RUNNING"
        return dict(s)

    def release(self, sandbox_id: str) -> dict[str, Any]:
        s = self._require(sandbox_id)
        s["status"] = "FREE"
        s["task_id"] = None
        s["workdir"] = None
        s["lease_id"] = None
        return dict(s)

    def mark_error(self, sandbox_id: str) -> dict[str, Any]:
        s = self._require(sandbox_id)
        s["status"] = "ERROR"
        return dict(s)

    def recover_error(self, sandbox_id: str) -> dict[str, Any]:
        s = self._require(sandbox_id)
        if s["status"] != "ERROR":
            raise SandboxError("not in ERROR")
        s["status"] = "FREE"
        s["task_id"] = None
        s["workdir"] = None
        s["lease_id"] = None
        return dict(s)

    def _require(self, sandbox_id: str) -> dict[str, Any]:
        s = self._slots.get(sandbox_id)
        if s is None:
            raise SandboxError(f"unknown sandbox {sandbox_id}")
        return s

    def snapshot(self) -> dict[str, Any]:
        by_status: dict[str, int] = {}
        for s in self._slots.values():
            by_status[s["status"]] = by_status.get(s["status"], 0) + 1
        return {
            "backend_requested": self.backend,
            "backend_effective": "logical",
            "total": len(self._slots),
            "by_status": by_status,
            "sandboxes": self.list_all(),
        }
