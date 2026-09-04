# -*- coding: utf-8 -*-
"""ParallelRuntime — T22. Glue Scheduler+Pool+Sandbox+Lease. 0% LLM."""
from __future__ import annotations

from typing import Any, Callable

from .lease_manager import LeaseManager
from .sandbox_manager import SandboxError, SandboxManager
from .task_queue import WorkerPool


class ParallelRuntime:
    """Runs tasks with slot + sandbox + lease. Logical only (no threads/SSH)."""

    def __init__(
        self,
        *,
        n_workers: int = 2,
        n_sandboxes: int | None = None,
        lease_ttl_s: float = 60.0,
        lease_clock: Any = None,
    ):
        self.pool = WorkerPool(n_workers=n_workers)
        self.sandboxes = SandboxManager(n_slots=n_sandboxes or n_workers)
        self.leases = LeaseManager(default_ttl_s=lease_ttl_s, clock=lease_clock)
        self.executions: list[dict[str, Any]] = []

    def submit(
        self,
        *,
        task_id: str | None = None,
        priority: int = 50,
        depends_on: list[str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.pool.queue.enqueue(
            task_id=task_id,
            priority=priority,
            depends_on=depends_on,
            payload=payload,
        )

    def run(
        self,
        handler: Callable[[dict[str, Any]], bool],
        *,
        max_steps: int = 1000,
    ) -> dict[str, Any]:
        """handler(ctx) -> success. ctx has task, sandbox, lease."""

        def wrapped(task: dict[str, Any]) -> bool:
            lease = self.leases.issue(
                subject_id=task["task_id"],
                subject_kind="task",
            )
            try:
                sb = self.sandboxes.allocate(
                    task["task_id"],
                    lease_id=lease["lease_id"],
                )
            except SandboxError as exc:
                self.leases.release(lease["lease_id"])
                self.executions.append(
                    {
                        "task_id": task["task_id"],
                        "ok": False,
                        "error": str(exc),
                    }
                )
                return False

            self.sandboxes.mark_running(sb["sandbox_id"])
            ctx = {
                "task": task,
                "sandbox": sb,
                "lease": lease,
            }
            ok = False
            try:
                if not self.leases.is_alive(lease["lease_id"]):
                    ok = False
                else:
                    ok = bool(handler(ctx))
            finally:
                self.sandboxes.release(sb["sandbox_id"])
                self.leases.release(lease["lease_id"])
                self.executions.append(
                    {
                        "task_id": task["task_id"],
                        "ok": ok,
                        "sandbox_id": sb["sandbox_id"],
                        "lease_id": lease["lease_id"],
                    }
                )
            return ok

        batch = self.pool.run_batch(wrapped, max_steps=max_steps)
        return {
            "batch": batch,
            "executions": list(self.executions),
            "sandboxes": self.sandboxes.snapshot(),
            "leases_expired": self.leases.sweep_expired(),
        }
