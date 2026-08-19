"""IntelligenceGateway — unique Loop path to LLM/memory.

Production: RouterHTTPGateway → Router Universal FastAPI.
Offline: MockIntelligenceGateway.
Loop MUST NOT call provider APIs directly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
import hashlib
import time
import uuid


@dataclass(frozen=True)
class GatewayRequest:
    task_id: str
    trace_id: str
    capability: str  # llm.complete | memory.recall | memory.capture
    payload: dict[str, Any] = field(default_factory=dict)
    policy: dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: f"REQ-{uuid.uuid4().hex[:12]}")

    def to_router_body(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "task_id": self.task_id,
            "trace_id": self.trace_id,
            "operation": self.capability,
            "policy": self.policy or {
                "max_cost": 0.05,
                "max_latency_ms": 30000,
                "required_capabilities": [],
            },
            "input": self.payload,
        }


@dataclass(frozen=True)
class GatewayResponse:
    request_id: str
    task_id: str
    trace_id: str
    status: str  # OK | DENY | ERROR | MOCK
    output: dict[str, Any] = field(default_factory=dict)
    provider: str | None = None
    evidence_hash: str | None = None


class IntelligenceGateway(Protocol):
    def execute(self, request: GatewayRequest) -> GatewayResponse:
        """Execute capability via Router or Mock. Never call LLM vendors here in Protocol."""
        ...

    def complete(self, prompt: str) -> str:
        """T26: unique LLM text path. Stub or router — never vendor import."""
        ...


class MockIntelligenceGateway:
    """Deterministic offline gateway for tests and PLAN_ONLY runs."""

    def __init__(self, fixed_text: str = "GATEWAY_STUB") -> None:
        self.fixed_text = fixed_text
        self.calls: list[GatewayRequest] = []

    def execute(self, request: GatewayRequest) -> GatewayResponse:
        self.calls.append(request)
        body = request.to_router_body()
        raw = f"{request.request_id}:{request.capability}:{sorted(body.get('input', {}).keys())}"
        ehash = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

        if request.capability == "llm.complete":
            output = {
                "text": self.fixed_text,
                "mock": True,
                "echo_task": request.task_id,
            }
        elif request.capability == "memory.recall":
            output = {"items": [], "mock": True}
        elif request.capability == "memory.capture":
            output = {"stored": True, "mock": True}
        else:
            return GatewayResponse(
                request_id=request.request_id,
                task_id=request.task_id,
                trace_id=request.trace_id,
                status="DENY",
                output={"reason": f"unknown_capability:{request.capability}"},
                provider="mock",
                evidence_hash=ehash,
            )

        return GatewayResponse(
            request_id=request.request_id,
            task_id=request.task_id,
            trace_id=request.trace_id,
            status="MOCK",
            output=output,
            provider="mock",
            evidence_hash=ehash,
        )

    def complete(self, prompt: str) -> str:
        req = make_request("t26", "llm.complete", {"prompt": str(prompt)})
        resp = self.execute(req)
        return str(resp.output.get("text") or self.fixed_text)


def make_request(
    task_id: str,
    capability: str,
    payload: dict[str, Any] | None = None,
    trace_id: str | None = None,
    policy: dict[str, Any] | None = None,
) -> GatewayRequest:
    return GatewayRequest(
        task_id=task_id,
        trace_id=trace_id or f"TRACE-{uuid.uuid4().hex[:10]}",
        capability=capability,
        payload=payload or {},
        policy=policy or {},
    )


if __name__ == "__main__":
    gw = MockIntelligenceGateway()
    text = gw.complete("hello")
    assert text == "GATEWAY_STUB", text
    print("ok", text)
