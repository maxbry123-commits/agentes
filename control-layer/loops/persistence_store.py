"""Persistencia registry + dlq + state JSONL · 0% LLM
SOURCE: P2
"""
from __future__ import annotations
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from loops.dlq import DLQItem, DeadLetterQueue
from loops.persist import JsonlStore
from loops.registry import LoopRegistry, RegistryEntry


class PersistenceStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.registry_path = self.root / "registry.jsonl"
        self.dlq_path = self.root / "dlq.jsonl"
        self.state_path = self.root / "state.jsonl"
        self.events_path = self.root / "events.jsonl"

    def save_registry_entry(self, e: RegistryEntry) -> None:
        JsonlStore(self.registry_path).append({
            "run_id": e.run_id, "loop_id": e.loop_id, "project_id": e.project_id,
            "agent_id": e.agent_id, "task_id": e.task_id, "state": e.state,
            "parent_run_id": e.parent_run_id, "meta": e.meta,
        })

    def save_dlq(self, item: DLQItem) -> None:
        JsonlStore(self.dlq_path).append({
            "run_id": item.run_id, "project_id": item.project_id,
            "agent_id": item.agent_id, "task_id": item.task_id,
            "state": item.state, "reason": item.reason,
            "errors": item.errors, "repair_count": item.repair_count,
            "enqueued_at": item.enqueued_at, "requeue_count": item.requeue_count,
        })

    def save_state(self, run_id: str, state: dict[str, Any]) -> None:
        JsonlStore(self.state_path).append({"run_id": run_id, **state})

    def save_event(self, event: dict[str, Any]) -> None:
        JsonlStore(self.events_path).append(event)

    def load_registry(self) -> list[dict[str, Any]]:
        return JsonlStore(self.registry_path).read_all()

    def load_dlq(self) -> list[dict[str, Any]]:
        return JsonlStore(self.dlq_path).read_all()

    def load_events(self, run_id: str | None = None) -> list[dict[str, Any]]:
        rows = JsonlStore(self.events_path).read_all()
        if run_id:
            return [r for r in rows if r.get("run_id") == run_id]
        return rows

    def hydrate_registry(self, reg: LoopRegistry) -> int:
        n = 0
        for row in self.load_registry():
            # last write wins — append-only log; rebuild by replaying
            e = RegistryEntry(
                run_id=row["run_id"], loop_id=row.get("loop_id", ""),
                project_id=row.get("project_id", ""), agent_id=row.get("agent_id", ""),
                task_id=row.get("task_id", ""), state=row.get("state", "CREATED"),
                parent_run_id=row.get("parent_run_id"), meta=row.get("meta") or {},
            )
            reg._by_run[e.run_id] = e
            n += 1
        return n

    def hydrate_dlq(self, dlq: DeadLetterQueue) -> int:
        n = 0
        for row in self.load_dlq():
            item = DLQItem(
                run_id=row["run_id"], project_id=row.get("project_id", ""),
                agent_id=row.get("agent_id", ""), task_id=row.get("task_id", ""),
                state=row.get("state", "FAILED"), reason=row.get("reason", ""),
                errors=row.get("errors") or [], repair_count=int(row.get("repair_count") or 0),
                enqueued_at=row.get("enqueued_at", ""), requeue_count=int(row.get("requeue_count") or 0),
            )
            dlq._items[item.run_id] = item
            n += 1
        return n
