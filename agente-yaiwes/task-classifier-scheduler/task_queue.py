# -*- coding: utf-8 -*-
"""TaskQueue + WorkerPool — T15. Slots over Scheduler. 0% LLM."""
from __future__ import annotations

from typing import Any, Callable

from .scheduler import Scheduler, SchedulerError


class TaskQueue:
    """FIFO-with-priority facade: enqueue → scheduler DAG."""

    def __init__(self, max_parallel: int = 1):
        self.scheduler = Scheduler(max_parallel=max_parallel)
        self._seq = 0

    def enqueue(
        self,
        *,
        task_id: str | None = None,
        priority: int = 50,
        depends_on: list[str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._seq += 1
        tid = task_id or f"tq_{self._seq:05d}"
        return self.scheduler.add(
            tid,
            priority=priority,
            depends_on=depends_on,
            payload=payload,
        )

    def size(self) -> int:
        return self.scheduler.snapshot()["total"]

    def pending_count(self) -> int:
        snap = self.scheduler.snapshot()
        bs = snap["by_status"]
        return bs.get("PENDING", 0) + bs.get("READY", 0) + bs.get("RUNNING", 0)


class WorkerPool:
    """Logical worker slots bound to Scheduler.max_parallel.

    Does not spawn threads/processes — slot accounting only (determinism).
    Real sandbox/SSH workers = later T16+.
    """

    def __init__(self, n_workers: int = 1):
        if n_workers < 1:
            raise ValueError("n_workers >= 1")
        self.n_workers = n_workers
        self.queue = TaskQueue(max_parallel=n_workers)
        self._slots: dict[int, str | None] = {i: None for i in range(n_workers)}

    @property
    def free_slots(self) -> int:
        return sum(1 for v in self._slots.values() if v is None)

    def assign(self) -> dict[str, Any] | None:
        """Claim next task into a free slot."""
        free = next((i for i, v in self._slots.items() if v is None), None)
        if free is None:
            return None
        task = self.queue.scheduler.claim_next()
        if task is None:
            return None
        self._slots[free] = task["task_id"]
        return {"slot": free, "task": task}

    def release(self, task_id: str, *,
                success: bool = True) -> dict[str, Any]:
        slot = next((i for i, v in self._slots.items() if v == task_id), None)
        if slot is not None:
            self._slots[slot] = None
        return self.queue.scheduler.complete(task_id, success=success)

    def run_batch(
        self,
        handler: Callable[[dict[str, Any]], bool],
        *,
        max_steps: int = 1000,
    ) -> dict[str, Any]:
        """Fill slots, run handler, release until idle."""
        steps = 0
        while steps < max_steps:
            progress = False
            while self.free_slots > 0:
                assigned = self.assign()
                if assigned is None:
                    break
                progress = True
                task = assigned["task"]
                ok = handler(task)
                self.release(task["task_id"], success=bool(ok))
                steps += 1
                if steps >= max_steps:
                    break
            if not progress:
                break
        return {
            "steps": steps,
            "slots": dict(self._slots),
            "scheduler": self.queue.scheduler.snapshot(),
        }
