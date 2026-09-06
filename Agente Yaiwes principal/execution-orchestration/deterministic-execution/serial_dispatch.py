"""Deterministic 1x1 task selection adapter for YAIWES.

Provenance:
- source pattern: maxbry123-commits/Agentes-motores-Wordflow-YAIWES
  Loop Engineer/Loop-Engineer/loop/runner.py
- source blob: daa32a5d6dfeb0d21a975b8a5b8384d68a8aa08e

This module ports only the proven source-order selection invariant.  It does not
import the Loop Engineer package and therefore does not duplicate its event
store/runtime.  YAIWES keeps execution, persistence and evidence in their own
layers.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Any, TypeVar

T = TypeVar("T")

_DONE = frozenset({"DONE", "PASSED", "VERIFIED_CLOSED", "COMPLETED"})
_PENDING = frozenset({"PENDING", "READY", "EN_CURSO", "IN_PROGRESS"})


def _field(task: Any, name: str, default: Any = None) -> Any:
    if isinstance(task, Mapping):
        return task.get(name, default)
    return getattr(task, name, default)


def task_id(task: Any) -> str:
    value = _field(task, "task_id", _field(task, "id", ""))
    return str(value) if value is not None else ""


def task_status(task: Any) -> str:
    return str(_field(task, "status", "PENDING")).upper()


def task_dependencies(task: Any) -> tuple[str, ...]:
    raw = _field(task, "depends_on", _field(task, "dependencies", ())) or ()
    return tuple(str(item) for item in raw)


def done_task_ids(tasks: Iterable[Any], durable_done: Iterable[str] = ()) -> set[str]:
    """Return declaratively completed ids plus durable completion ids."""
    done = {str(item) for item in durable_done}
    for task in tasks:
        tid = task_id(task)
        if tid and task_status(task) in _DONE:
            done.add(tid)
    return done


def select_next_task(tasks: Iterable[T], durable_done: Iterable[str] = ()) -> T | None:
    """Return the first runnable pending task in source order.

    A task is runnable only when all declared dependencies are complete.  The
    function is pure: it selects exactly zero or one item and performs no side
    effects.
    """
    materialized = list(tasks)
    done = done_task_ids(materialized, durable_done)
    for task in materialized:
        tid = task_id(task)
        if not tid or tid in done or task_status(task) not in _PENDING:
            continue
        if all(dep in done for dep in task_dependencies(task)):
            return task
    return None


def dispatch_once(
    tasks: Iterable[T],
    dispatch: Callable[[T], Any],
    *,
    durable_done: Iterable[str] = (),
) -> dict[str, Any]:
    """Dispatch at most one runnable task and report the deterministic result."""
    selected = select_next_task(tasks, durable_done)
    if selected is None:
        return {"ok": False, "action": "blocked_or_empty", "task_id": None}
    result = dispatch(selected)
    return {
        "ok": True,
        "action": "dispatched_once",
        "task_id": task_id(selected),
        "result": result,
    }
