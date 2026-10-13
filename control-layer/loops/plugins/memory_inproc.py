"""In-memory MemoryPlugin — Fase 5 mínima · 0% LLM"""
from __future__ import annotations
from typing import Any

from loops.plugins.base import MemoryPlugin


class InMemoryPlugin(MemoryPlugin):
    def __init__(self) -> None:
        self.events: list[Any] = []
        self.scopes: dict[str, dict[str, Any]] = {}
        self.checkpoints: dict[str, dict[str, Any]] = {}

    def append_event(self, event: Any) -> bool:
        self.events.append(event)
        return True

    def read_scope(self, scope: str, key: str, limit: int = 50) -> list[Any]:
        bucket = self.scopes.get(scope) or {}
        val = bucket.get(key)
        if val is None:
            return []
        if isinstance(val, list):
            return val[-limit:]
        return [val]

    def write_scope(self, scope: str, key: str, value: Any, ttl: int | None = None) -> bool:
        self.scopes.setdefault(scope, {})[key] = value
        return True

    def checkpoint(self, run_id: str, snapshot: dict[str, Any]) -> str:
        cid = f"cp-{run_id}-{len(self.checkpoints)}"
        self.checkpoints[cid] = dict(snapshot)
        return cid

    def restore_checkpoint(self, checkpoint_id: str) -> dict[str, Any] | None:
        return self.checkpoints.get(checkpoint_id)
