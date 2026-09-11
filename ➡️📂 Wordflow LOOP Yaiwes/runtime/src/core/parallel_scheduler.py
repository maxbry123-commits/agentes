"""Deterministic DAG batch planner with priority, dedup and backpressure."""
from __future__ import annotations

import graphlib
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


class SchedulerError(ValueError):
    pass


@dataclass(frozen=True)
class TaskEnvelope:
    task_id: str
    priority: int
    idempotency_key: str
    depends_on: Tuple[str, ...] = ()
    payload: Any = None


@dataclass(frozen=True)
class SchedulePlan:
    batches: Tuple[Tuple[str, ...], ...]
    idempotency_index: Dict[str, str]
    max_concurrency: int


def plan_tasks(
    tasks: List[TaskEnvelope],
    *,
    max_concurrency: int = 4,
    max_queue: int = 100,
) -> SchedulePlan:
    if max_concurrency < 1 or max_queue < 1:
        raise SchedulerError("invalid limits")
    if len(tasks) > max_queue:
        raise SchedulerError("BACKPRESSURE_QUEUE_LIMIT")

    by_id: Dict[str, TaskEnvelope] = {}
    by_key: Dict[str, str] = {}
    for task in tasks:
        if not task.task_id or not task.idempotency_key:
            raise SchedulerError("task_id and idempotency_key required")
        if task.task_id in by_id:
            raise SchedulerError("DUPLICATE_TASK_ID")
        if task.idempotency_key in by_key:
            raise SchedulerError("DUPLICATE_IDEMPOTENCY_KEY")
        by_id[task.task_id] = task
        by_key[task.idempotency_key] = task.task_id

    for task in tasks:
        for dependency in task.depends_on:
            if dependency not in by_id:
                raise SchedulerError("MISSING_DEPENDENCY")

    sorter = graphlib.TopologicalSorter(
        {task.task_id: set(task.depends_on) for task in tasks}
    )
    try:
        sorter.prepare()
    except graphlib.CycleError as exc:
        raise SchedulerError("CYCLE_DETECTED") from exc

    batches = []
    while sorter.is_active():
        ready = list(sorter.get_ready())
        ready.sort(key=lambda task_id: (-by_id[task_id].priority, task_id))
        if not ready:
            raise SchedulerError("NO_READY_TASKS")
        for index in range(0, len(ready), max_concurrency):
            batches.append(tuple(ready[index : index + max_concurrency]))
        sorter.done(*ready)

    return SchedulePlan(tuple(batches), dict(by_key), max_concurrency)
