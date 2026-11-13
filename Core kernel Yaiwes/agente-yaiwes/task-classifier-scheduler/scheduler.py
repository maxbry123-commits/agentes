# -*- coding: utf-8 -*-
"""Scheduler — T14. DAG + priority ready-queue. 0% LLM."""
from __future__ import annotations

from typing import Any, Callable

Status = str  # PENDING READY RUNNING DONE FAILED CANCELLED


class SchedulerError(Exception):
    pass


class Scheduler:
    """In-process scheduler: register tasks, resolve ready set, dispatch order.

    Priority: higher number = sooner (100 first).
    Ties broken by task_id lexicographic for determinism.
    """

    def __init__(self, max_parallel: int = 1):
        if max_parallel < 1:
            raise ValueError("max_parallel >= 1")
        self.max_parallel = max_parallel
        self._tasks: dict[str, dict[str, Any]] = {}
        self._running: set[str] = set()

    def add(
        self,
        task_id: str,
        *,
        priority: int = 50,
        depends_on: list[str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not task_id:
            raise SchedulerError("task_id required")
        if task_id in self._tasks:
            raise SchedulerError(f"duplicate task_id={task_id}")
        if priority < 0 or priority > 100:
            raise SchedulerError("priority 0..100")
        deps = list(depends_on or [])
        task = {
            "task_id": task_id,
            "priority": int(priority),
            "depends_on": deps,
            "status": "PENDING",
            "payload": dict(payload or {}),
        }
        self._tasks[task_id] = task
        self._refresh_ready()
        return dict(task)

    def _deps_satisfied(self, task: dict[str, Any]) -> bool:
        for d in task.get("depends_on") or []:
            dep = self._tasks.get(d)
            if dep is None:
                return False
            if dep["status"] != "DONE":
                return False
        return True

    def _refresh_ready(self) -> None:
        for t in self._tasks.values():
            if t["status"] == "PENDING" and self._deps_satisfied(t):
                t["status"] = "READY"
            elif t["status"] == "READY" and not self._deps_satisfied(t):
                # should not happen if we only advance forward
                t["status"] = "PENDING"

    def ready_queue(self) -> list[dict[str, Any]]:
        self._refresh_ready()
        ready = [t for t in self._tasks.values() if t["status"] == "READY"]
        ready.sort(key=lambda t: (-t["priority"], t["task_id"]))
        return [dict(t) for t in ready]

    def claim_next(self) -> dict[str, Any] | None:
        """Move highest priority READY → RUNNING if under max_parallel."""
        if len(self._running) >= self.max_parallel:
            return None
        q = self.ready_queue()
        if not q:
            return None
        tid = q[0]["task_id"]
        self._tasks[tid]["status"] = "RUNNING"
        self._running.add(tid)
        return dict(self._tasks[tid])

    def complete(self, task_id: str, *,
                 success: bool = True) -> dict[str, Any]:
        t = self._tasks.get(task_id)
        if t is None:
            raise SchedulerError(f"unknown task {task_id}")
        if t["status"] != "RUNNING":
            raise SchedulerError(f"task {task_id} not RUNNING")
        t["status"] = "DONE" if success else "FAILED"
        self._running.discard(task_id)
        self._refresh_ready()
        return dict(t)

    def cancel(self, task_id: str) -> dict[str, Any]:
        t = self._tasks.get(task_id)
        if t is None:
            raise SchedulerError(f"unknown task {task_id}")
        if t["status"] in ("DONE", "FAILED", "CANCELLED"):
            return dict(t)
        t["status"] = "CANCELLED"
        self._running.discard(task_id)
        return dict(t)

    def run_until_idle(
        self,
        handler: Callable[[dict[str, Any]], bool],
        *,
        max_steps: int = 1000,
    ) -> dict[str, Any]:
        """Deterministic loop: claim → handler → complete. handler returns success bool."""
        steps = 0
        while steps < max_steps:
            task = self.claim_next()
            if task is None:
                if self._running:
                    break  # would block on parallel workers (single-thread idle)
                if any(t["status"] in ("PENDING", "READY") for t in self._tasks.values()):
                    # blocked on failed deps or missing
                    break
                break
            ok = handler(task)
            self.complete(task["task_id"], success=bool(ok))
            steps += 1
        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        by_status: dict[str, int] = {}
        for t in self._tasks.values():
            by_status[t["status"]] = by_status.get(t["status"], 0) + 1
        return {
            "total": len(self._tasks),
            "by_status": by_status,
            "running": sorted(self._running),
            "max_parallel": self.max_parallel,
            "tasks": {k: dict(v) for k, v in self._tasks.items()},
        }
