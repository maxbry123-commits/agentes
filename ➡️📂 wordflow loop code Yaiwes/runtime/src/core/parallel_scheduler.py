"""Deterministic DAG planner and bounded executor."""
from __future__ import annotations

import asyncio
import graphlib
import json
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, MutableMapping, Tuple


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
    aliases: Dict[str, str]


@dataclass(frozen=True)
class TaskResult:
    task_id: str
    canonical_task_id: str
    status: str
    output: Any


def _payload_fingerprint(payload: Any) -> str:
    try:
        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise SchedulerError("PAYLOAD_NOT_CANONICAL_JSON") from exc


def plan_tasks(
    tasks: List[TaskEnvelope],
    *,
    max_concurrency: int = 4,
    max_queue: int = 100,
) -> SchedulePlan:
    if (
        not isinstance(max_concurrency, int)
        or isinstance(max_concurrency, bool)
        or not isinstance(max_queue, int)
        or isinstance(max_queue, bool)
        or max_concurrency < 1
        or max_queue < 1
    ):
        raise SchedulerError("invalid limits")
    if len(tasks) > max_queue:
        raise SchedulerError("BACKPRESSURE_QUEUE_LIMIT")

    by_id: Dict[str, TaskEnvelope] = {}
    by_key: Dict[str, str] = {}
    aliases: Dict[str, str] = {}
    signatures: Dict[str, Tuple[int, Tuple[str, ...], str]] = {}
    seen_task_ids = set()
    for task in tasks:
        if not task.task_id or not task.idempotency_key:
            raise SchedulerError("task_id and idempotency_key required")
        if (
            not isinstance(task.priority, int)
            or isinstance(task.priority, bool)
            or not 0 <= task.priority <= 1000
        ):
            raise SchedulerError("INVALID_PRIORITY")
        if task.task_id in seen_task_ids:
            raise SchedulerError("DUPLICATE_TASK_ID")
        seen_task_ids.add(task.task_id)
        if task.idempotency_key in by_key:
            canonical_id = by_key[task.idempotency_key]
            signature = (
                task.priority,
                tuple(task.depends_on),
                _payload_fingerprint(task.payload),
            )
            if signatures[task.idempotency_key] != signature:
                raise SchedulerError("IDEMPOTENCY_KEY_CONFLICT")
            aliases[task.task_id] = canonical_id
            continue
        by_id[task.task_id] = task
        by_key[task.idempotency_key] = task.task_id
        aliases[task.task_id] = task.task_id
        signatures[task.idempotency_key] = (
            task.priority,
            tuple(task.depends_on),
            _payload_fingerprint(task.payload),
        )

    all_task_ids = set(aliases)
    normalized_dependencies: Dict[str, set[str]] = {}
    for task in by_id.values():
        dependencies = set()
        for dependency in task.depends_on:
            if dependency not in all_task_ids:
                raise SchedulerError("MISSING_DEPENDENCY")
            dependencies.add(aliases[dependency])
        normalized_dependencies[task.task_id] = dependencies

    sorter = graphlib.TopologicalSorter(normalized_dependencies)
    try:
        sorter.prepare()
    except graphlib.CycleError as exc:
        raise SchedulerError("CYCLE_DETECTED") from exc

    batches = []
    while sorter.is_active():
        ready = list(sorter.get_ready())
        # The canonical Kernel and Mavis queues use the same convention:
        # lower numeric values are more urgent.
        ready.sort(key=lambda task_id: (by_id[task_id].priority, task_id))
        if not ready:
            raise SchedulerError("NO_READY_TASKS")
        for index in range(0, len(ready), max_concurrency):
            batches.append(tuple(ready[index : index + max_concurrency]))
        sorter.done(*ready)

    return SchedulePlan(
        tuple(batches),
        dict(by_key),
        max_concurrency,
        dict(aliases),
    )


async def execute_tasks(
    tasks: List[TaskEnvelope],
    worker_fn: Callable[[TaskEnvelope], Awaitable[Any]],
    *,
    max_concurrency: int = 4,
    max_queue: int = 100,
    completed_by_key: MutableMapping[str, Any] | None = None,
) -> Tuple[TaskResult, ...]:
    """Execute one planned DAG with bounded fan-out and fail-closed fan-in."""

    plan = plan_tasks(
        tasks,
        max_concurrency=max_concurrency,
        max_queue=max_queue,
    )
    by_id = {
        task.task_id: task
        for task in tasks
        if plan.aliases[task.task_id] == task.task_id
    }
    completed = completed_by_key if completed_by_key is not None else {}
    results: List[TaskResult] = []
    result_by_id: Dict[str, Any] = {}

    for batch in plan.batches:
        async def run(task_id: str) -> TaskResult:
            task = by_id[task_id]
            for dependency in task.depends_on:
                canonical_dependency = plan.aliases[dependency]
                if canonical_dependency not in result_by_id:
                    raise SchedulerError("DEPENDENCY_NOT_COMPLETED")
            if task.idempotency_key in completed:
                output = completed[task.idempotency_key]
                return TaskResult(task_id, task_id, "IDEMPOTENT_REPLAY", output)
            output = await worker_fn(task)
            completed[task.idempotency_key] = output
            return TaskResult(task_id, task_id, "COMPLETED", output)

        batch_results = await asyncio.gather(*(run(task_id) for task_id in batch))
        for result in batch_results:
            result_by_id[result.task_id] = result.output
            results.append(result)

    for alias_id, canonical_id in plan.aliases.items():
        if alias_id == canonical_id:
            continue
        output = result_by_id[canonical_id]
        results.append(TaskResult(alias_id, canonical_id, "DEDUPLICATED", output))
    return tuple(results)
