"""In-memory GraphPlugin — experience graph mínimo · 0% LLM"""
from __future__ import annotations
from typing import Any

from loops.plugins.base import GraphPlugin


class InMemoryGraphPlugin(GraphPlugin):
    def __init__(self) -> None:
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: list[tuple[str, str, str, dict]] = []
        self.events: list[Any] = []

    def upsert_node(self, node_type: str, node_id: str, attrs: dict[str, Any]) -> bool:
        self.nodes[node_id] = {"type": node_type, **attrs}
        return True

    def upsert_edge(self, from_id: str, to_id: str, relation: str, attrs: dict[str, Any] | None = None) -> bool:
        self.edges.append((from_id, to_id, relation, dict(attrs or {})))
        return True

    def query_similar(self, task_fingerprint: str, limit: int = 5) -> list[Any]:
        # naive: nodes with matching fingerprint attr
        hits = [
            {"id": nid, **data}
            for nid, data in self.nodes.items()
            if data.get("fingerprint") == task_fingerprint or data.get("task_fingerprint") == task_fingerprint
        ]
        return hits[:limit]

    def on_event(self, event: Any) -> bool:
        self.events.append(event)
        # auto node for loop runs
        run_id = getattr(event, "run_id", None) or (event.get("run_id") if isinstance(event, dict) else None)
        etype = getattr(event, "type", None) or (event.get("type") if isinstance(event, dict) else None)
        if run_id and etype:
            self.upsert_node("loop_run", str(run_id), {"last_event": etype})
        return True
