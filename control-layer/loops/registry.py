"""Loop Registry — índice central de runs · 0% LLM
SOURCE: Fase 4 arquitectura loops
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from loops.contracts.types import LoopContext, TERMINAL


@dataclass
class RegistryEntry:
    run_id: str
    loop_id: str
    project_id: str
    agent_id: str
    task_id: str
    state: str
    parent_run_id: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


class LoopRegistry:
    def __init__(self) -> None:
        self._by_run: dict[str, RegistryEntry] = {}

    def upsert(self, ctx: LoopContext, **meta: Any) -> RegistryEntry:
        e = RegistryEntry(
            run_id=ctx.run_id,
            loop_id=ctx.loop_id,
            project_id=ctx.project_id,
            agent_id=ctx.agent_id,
            task_id=ctx.task_id,
            state=ctx.state,
            parent_run_id=ctx.parent_run_id,
            meta=dict(meta),
        )
        self._by_run[ctx.run_id] = e
        return e

    def get(self, run_id: str) -> RegistryEntry | None:
        return self._by_run.get(run_id)

    def find_by_project(self, project_id: str) -> list[RegistryEntry]:
        return [e for e in self._by_run.values() if e.project_id == project_id]

    def find_by_agent(self, agent_id: str) -> list[RegistryEntry]:
        return [e for e in self._by_run.values() if e.agent_id == agent_id]

    def find_by_task(self, task_id: str) -> list[RegistryEntry]:
        return [e for e in self._by_run.values() if e.task_id == task_id]

    def find_active(self) -> list[RegistryEntry]:
        return [e for e in self._by_run.values() if e.state not in TERMINAL]

    def find_failed(self) -> list[RegistryEntry]:
        return [e for e in self._by_run.values() if e.state in ("FAILED", "ESCALATED")]

    def find_parent(self, parent_run_id: str) -> list[RegistryEntry]:
        return [e for e in self._by_run.values() if e.parent_run_id == parent_run_id]

    def remove(self, run_id: str) -> bool:
        return self._by_run.pop(run_id, None) is not None

    def all(self) -> list[RegistryEntry]:
        return list(self._by_run.values())
