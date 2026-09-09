"""Dead Letter Queue — runs fallidos para reinyección · 0% LLM
SOURCE: Fase 4
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class DLQItem:
    run_id: str
    project_id: str
    agent_id: str
    task_id: str
    state: str
    reason: str
    errors: list[Any] = field(default_factory=list)
    evidence: list[Any] = field(default_factory=list)
    repair_count: int = 0
    strategies_used: list[str] = field(default_factory=list)
    checkpoint_id: str | None = None
    budget_snapshot: dict[str, Any] = field(default_factory=dict)
    enqueued_at: str = field(default_factory=_now)
    requeue_count: int = 0


class DeadLetterQueue:
    def __init__(self) -> None:
        self._items: dict[str, DLQItem] = {}

    def enqueue(self, item: DLQItem) -> None:
        self._items[item.run_id] = item

    def get(self, run_id: str) -> DLQItem | None:
        return self._items.get(run_id)

    def list_all(self) -> list[DLQItem]:
        return list(self._items.values())

    def requeue(self, run_id: str) -> DLQItem | None:
        item = self._items.pop(run_id, None)
        if item:
            item.requeue_count += 1
        return item

    def drop(self, run_id: str) -> bool:
        return self._items.pop(run_id, None) is not None
