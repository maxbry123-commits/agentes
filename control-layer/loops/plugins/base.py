"""Plugin ABCs + NoOp adapters — conexión lista, backends reales después.
SOURCE: memory_plugin.schema · graph_plugin.schema · 0% LLM
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any


class MemoryPlugin(ABC):
    @abstractmethod
    def append_event(self, event: Any) -> bool: ...

    @abstractmethod
    def read_scope(self, scope: str, key: str, limit: int = 50) -> list[Any]: ...

    @abstractmethod
    def write_scope(self, scope: str, key: str, value: Any, ttl: int | None = None) -> bool: ...

    @abstractmethod
    def checkpoint(self, run_id: str, snapshot: dict[str, Any]) -> str: ...

    @abstractmethod
    def restore_checkpoint(self, checkpoint_id: str) -> dict[str, Any] | None: ...


class NoOpMemoryPlugin(MemoryPlugin):
    def append_event(self, event: Any) -> bool:
        return True

    def read_scope(self, scope: str, key: str, limit: int = 50) -> list[Any]:
        return []

    def write_scope(self, scope: str, key: str, value: Any, ttl: int | None = None) -> bool:
        return True

    def checkpoint(self, run_id: str, snapshot: dict[str, Any]) -> str:
        return f"noop-cp-{run_id}"

    def restore_checkpoint(self, checkpoint_id: str) -> dict[str, Any] | None:
        return None


class GraphPlugin(ABC):
    @abstractmethod
    def upsert_node(self, node_type: str, node_id: str, attrs: dict[str, Any]) -> bool: ...

    @abstractmethod
    def upsert_edge(self, from_id: str, to_id: str, relation: str, attrs: dict[str, Any] | None = None) -> bool: ...

    @abstractmethod
    def query_similar(self, task_fingerprint: str, limit: int = 5) -> list[Any]: ...

    @abstractmethod
    def on_event(self, event: Any) -> bool: ...


class NoOpGraphPlugin(GraphPlugin):
    def upsert_node(self, node_type: str, node_id: str, attrs: dict[str, Any]) -> bool:
        return True

    def upsert_edge(self, from_id: str, to_id: str, relation: str, attrs: dict[str, Any] | None = None) -> bool:
        return True

    def query_similar(self, task_fingerprint: str, limit: int = 5) -> list[Any]:
        return []

    def on_event(self, event: Any) -> bool:
        return True
