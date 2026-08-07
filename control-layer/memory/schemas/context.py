"""MemoryContext · Namespace · MemoryRecord · contratos núcleo (0% LLM)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class MemoryContext:
    tenant_id: str = "system"
    project_id: str = "default"
    agent_id: str = "default"
    workflow_id: str = ""
    task_id: str = ""
    session_id: str = ""
    memory_scope: str = "project"  # private | project | global
    memory_version: int = 0
    permissions: tuple[str, ...] = ("read", "write")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MemoryNamespace:
    """Determinista: tenant/project[/agent]."""

    value: str

    @staticmethod
    def from_context(ctx: MemoryContext) -> "MemoryNamespace":
        parts = [ctx.tenant_id, ctx.project_id]
        if ctx.memory_scope == "private":
            parts.append("agent")
            parts.append(ctx.agent_id)
        elif ctx.memory_scope == "global":
            parts = [ctx.tenant_id, "global"]
        else:
            parts.append("project")
        return MemoryNamespace(value="/".join(parts))


@dataclass
class MemoryRecord:
    id: str
    content: str
    type: str  # raw|fact|episodic|semantic|procedure|doc
    namespace: str
    project_id: str = ""
    agent_id: str = ""
    source: str = ""
    confidence: float = 1.0
    importance: float = 0.5
    version: int = 0
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
