"""Deterministic task contract compiler for CODE_GRAPH_ARCHITECTURE_PROGRAMMING_LOOP.

No network I/O, no LLM decisions, no deployment. Produces a manifest compatible
with runtime/src/core/dag_engine.py while keeping Director tasks and generated
tasks explicitly separated.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Literal

TaskSource = Literal["director", "generated"]
TaskStatus = Literal["pending", "ready", "running", "blocked", "passed", "failed"]
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class TaskContractError(ValueError):
    """Fail-closed validation error for task contracts."""


@dataclass(frozen=True)
class CodeTask:
    task_id: str
    source: TaskSource
    capability: str
    owner_role: str
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    priority: int = 100
    destination_candidate: str = ""
    sandbox_required: bool = True
    tests: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    idempotency_key: str = ""
    retry_limit: int = 2
    status: TaskStatus = "pending"


def validate_task(task: CodeTask) -> None:
    if not _ID.fullmatch(task.task_id):
        raise TaskContractError("invalid task_id")
    if task.source not in ("director", "generated"):
        raise TaskContractError("invalid source")
    if not task.capability.strip() or not task.owner_role.strip():
        raise TaskContractError("capability and owner_role are required")
    if not 0 <= task.priority <= 1000:
        raise TaskContractError("priority out of range")
    if not 0 <= task.retry_limit <= 20:
        raise TaskContractError("retry_limit out of range")
    if task.task_id in task.depends_on:
        raise TaskContractError("task cannot depend on itself")


def compile_task_graph(tasks: List[CodeTask]) -> Dict[str, Any]:
    """Compile validated tasks into a deterministic DAG manifest.

    The returned ``nodes`` object is directly consumable by ``DAGEngine``.
    ``director_tasks`` and ``generated_tasks`` are separate source-of-truth lists.
    """
    if not tasks:
        raise TaskContractError("at least one task required")

    by_id: Dict[str, CodeTask] = {}
    for task in tasks:
        validate_task(task)
        if task.task_id in by_id:
            raise TaskContractError(f"duplicate task_id: {task.task_id}")
        by_id[task.task_id] = task

    missing = sorted({
        dep for task in tasks for dep in task.depends_on if dep not in by_id
    })
    if missing:
        raise TaskContractError("missing dependencies: " + ", ".join(missing))

    nodes: Dict[str, Any] = {}
    for task_id in sorted(by_id):
        task = by_id[task_id]
        nodes[task_id] = {
            "depends_on": sorted(set(task.depends_on)),
            "payload": {
                "source": task.source,
                "capability": task.capability,
                "owner_role": task.owner_role,
                "inputs": list(task.inputs),
                "outputs": list(task.outputs),
                "priority": task.priority,
                "destination_candidate": task.destination_candidate,
                "sandbox_required": task.sandbox_required,
                "tests": list(task.tests),
                "evidence": list(task.evidence),
                "idempotency_key": task.idempotency_key or task.task_id,
                "retry_limit": task.retry_limit,
                "status": task.status,
            },
        }

    return {
        "director_tasks": sorted(t.task_id for t in tasks if t.source == "director"),
        "generated_tasks": sorted(t.task_id for t in tasks if t.source == "generated"),
        "nodes": nodes,
    }
