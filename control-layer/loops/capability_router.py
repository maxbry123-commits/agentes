"""CapabilityRequest → Agent/Model resolution · 0% LLM
SOURCE: P2 · Router real mínimo del control-layer
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from loops.contracts.capability import CapabilityRequest, CapabilityName


@dataclass
class AgentCapability:
    agent_id: str
    capabilities: list[str]
    priority: int = 100
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResolveResult:
    ok: bool
    agent_id: str | None = None
    reason: str = ""


class CapabilityRouter:
    """Registra agentes por capability y resuelve requests."""

    def __init__(self) -> None:
        self._agents: list[AgentCapability] = []

    def register(self, agent_id: str, capabilities: list[str], priority: int = 100, **meta: Any) -> None:
        self._agents.append(AgentCapability(
            agent_id=agent_id, capabilities=list(capabilities), priority=priority, meta=meta
        ))

    def resolve(self, req: CapabilityRequest) -> ResolveResult:
        cap = req.capability
        candidates = [a for a in self._agents if cap in a.capabilities]
        if not candidates:
            return ResolveResult(ok=False, reason=f"no agent for capability={cap}")
        candidates.sort(key=lambda a: a.priority)
        chosen = candidates[0]
        req.resolved_by = chosen.agent_id
        req.status = "resolved"
        return ResolveResult(ok=True, agent_id=chosen.agent_id, reason="ok")

    def list_for(self, capability: str) -> list[str]:
        return [a.agent_id for a in self._agents if capability in a.capabilities]
