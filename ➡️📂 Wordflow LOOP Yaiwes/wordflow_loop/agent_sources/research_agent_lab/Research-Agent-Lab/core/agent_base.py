from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from core.artifact_store import ArtifactStore
from core.state import ResearchState
from tools.tool_registry import ToolRegistry


class MemoryStore(Protocol):
    def write(self, scope: str, kind: str, payload: dict[str, Any]) -> None:
        ...

    def retrieve(self, scope: str, query: str, limit: int = 10) -> list[dict[str, Any]]:
        ...


@dataclass(slots=True)
class AgentContext:
    artifact_store: ArtifactStore
    memory_store: MemoryStore
    tool_registry: ToolRegistry
    settings: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AgentResult:
    notes: list[str] = field(default_factory=list)
    artifacts: dict[str, list[str]] = field(default_factory=dict)
    values: dict[str, Any] = field(default_factory=dict)


class Agent:
    name = "agent"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        raise NotImplementedError
