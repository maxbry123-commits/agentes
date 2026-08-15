"""EnginePort — OpenClaw/Hermes as intermediate reasoners only.

They sit between Wordflow and LLM: Loop may ask EnginePort.reason()
when policy requires structured reasoning. Engines MUST route LLM
calls through IntelligenceGateway (never direct vendor APIs).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from wordflow_kernel.gateway.intelligence import IntelligenceGateway, GatewayRequest, make_request


@dataclass(frozen=True)
class EngineRequest:
    task_id: str
    trace_id: str
    messages: list[dict[str, str]]
    policy: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EngineResult:
    engine_id: str
    status: str  # OK | DENY | ERROR | STUB
    content: str
    meta: dict[str, Any] = field(default_factory=dict)


class EnginePort(Protocol):
    engine_id: str

    def reason(self, request: EngineRequest, gateway: IntelligenceGateway) -> EngineResult:
        ...


class EngineRegistry:
    def __init__(self) -> None:
        self._engines: dict[str, EnginePort] = {}

    def register(self, engine: EnginePort) -> None:
        self._engines[engine.engine_id] = engine

    def get(self, engine_id: str) -> EnginePort | None:
        return self._engines.get(engine_id)

    def list_ids(self) -> list[str]:
        return sorted(self._engines.keys())

    def reason(
        self,
        engine_id: str,
        request: EngineRequest,
        gateway: IntelligenceGateway,
    ) -> EngineResult:
        eng = self.get(engine_id)
        if eng is None:
            return EngineResult(
                engine_id=engine_id,
                status="DENY",
                content="",
                meta={"reason": "engine_not_registered"},
            )
        return eng.reason(request, gateway)
