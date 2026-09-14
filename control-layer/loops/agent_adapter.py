"""Agent-agnostic adapter — cualquier agente via capability · 0% LLM
SOURCE: auditoría multiagente nativo
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable

from loops.capability_router import CapabilityRouter, ResolveResult
from loops.contracts.capability import CapabilityRequest


@dataclass
class AgentExecResult:
    ok: bool
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    tokens_used: int = 0


class AgentRuntime(ABC):
    """Contrato mínimo: cualquier agente (temporal, openclaw, custom)."""

    agent_id: str
    capabilities: list[str]

    @abstractmethod
    def execute(self, capability: str, payload: dict[str, Any]) -> AgentExecResult: ...


class CallableAgent(AgentRuntime):
    """Envuelve una función/callable como agente."""

    def __init__(self, agent_id: str, capabilities: list[str], fn: Callable[[str, dict], AgentExecResult]):
        self.agent_id = agent_id
        self.capabilities = capabilities
        self._fn = fn

    def execute(self, capability: str, payload: dict[str, Any]) -> AgentExecResult:
        if capability not in self.capabilities:
            return AgentExecResult(ok=False, error=f"capability {capability} not supported")
        return self._fn(capability, payload)


class AgentAdapter:
    """Registro + resolve + execute. Loop Engine no conoce agentes concretos."""

    def __init__(self, router: CapabilityRouter | None = None) -> None:
        self.router = router or CapabilityRouter()
        self._runtimes: dict[str, AgentRuntime] = {}

    def register_runtime(self, runtime: AgentRuntime, priority: int = 100) -> None:
        self._runtimes[runtime.agent_id] = runtime
        self.router.register(runtime.agent_id, runtime.capabilities, priority=priority)

    def dispatch(self, req: CapabilityRequest, payload: dict[str, Any] | None = None) -> AgentExecResult:
        res: ResolveResult = self.router.resolve(req)
        if not res.ok or not res.agent_id:
            return AgentExecResult(ok=False, error=res.reason)
        rt = self._runtimes.get(res.agent_id)
        if not rt:
            return AgentExecResult(ok=False, error=f"runtime missing for {res.agent_id}")
        return rt.execute(req.capability, payload or {})
