"""Router Universal — declarative contracts (no provider logic inside Wordflow)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RouterNodeContract:
    node_id: str
    kind: str  # llm | memory | mcp | github | hf | agent
    endpoint_ref: str  # env/url ref, not secret
    capabilities: tuple[str, ...] = ()
    policy: tuple[tuple[str, str], ...] = ()


@dataclass
class RouteRequest:
    task_id: str
    trace_id: str
    capability: str
    payload: dict[str, Any]
    policy: dict[str, Any] = field(default_factory=dict)


@dataclass
class RouteResponse:
    status: str
    provider: str
    output: dict[str, Any]
    evidence_hash: str = ""
    detail: dict[str, Any] = field(default_factory=dict)
