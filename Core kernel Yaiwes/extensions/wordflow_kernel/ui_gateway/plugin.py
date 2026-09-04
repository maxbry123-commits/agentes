"""UI Gateway Plugin — provisional UI → kernel → agents.

Default path: ingest + OpenClaw/Hermes stubs via MockIntelligenceGateway.
Does not embed a React front. llm_control=DENY. No vendor LLM.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class UIMessage:
    session_id: str
    text: str
    role: str = "user"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class UIResponse:
    status: str
    text: str
    mission_id: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)


def _route_kernel(msg: UIMessage) -> UIResponse:
    """UI → handle_message(ingest) → EnginePort stubs. Fail-closed."""
    ingest_out: dict[str, Any]
    try:
        from wordflow_kernel.handle_message import handle_message
    except ImportError:
        from extensions.wordflow_kernel.handle_message import handle_message  # type: ignore

    ingest_out = handle_message(
        {
            "action": "ingest",
            "payload": {
                "raw_text": msg.text,
                "source_type": "ui",
                "session_id": msg.session_id,
            },
        }
    )

    agents: dict[str, Any] = {}
    try:
        try:
            from wordflow_kernel.gateway.intelligence import MockIntelligenceGateway
            from wordflow_kernel.engines import (
                EngineRegistry,
                EngineRequest,
                HermesEngine,
                OpenClawEngine,
            )
        except ImportError:
            from extensions.wordflow_kernel.gateway.intelligence import MockIntelligenceGateway
            from extensions.wordflow_kernel.engines import (
                EngineRegistry,
                EngineRequest,
                HermesEngine,
                OpenClawEngine,
            )

        gw = MockIntelligenceGateway(fixed_text="UI_AGENT_STUB")
        reg = EngineRegistry()
        reg.register(OpenClawEngine())
        reg.register(HermesEngine())
        req = EngineRequest(
            task_id=msg.session_id or "ui",
            trace_id=f"ui-{msg.session_id}",
            messages=[{"role": msg.role, "content": msg.text}],
            context={"ui": True, "session_id": msg.session_id},
            policy={"llm_control": "DENY", "vendor": "DENY"},
        )
        for eid in reg.list_ids():
            res = reg.reason(eid, req, gw)
            agents[eid] = {
                "engine_id": res.engine_id,
                "status": res.status,
                "invoked": True,
                "vendor_call": False,
            }
    except Exception as exc:  # noqa: BLE001
        agents = {"ok": False, "error": str(exc), "invoked": False}

    ingest_ok = bool(ingest_out.get("ok"))
    agents_ok = isinstance(agents, dict) and all(
        isinstance(v, dict) and v.get("invoked") for v in agents.values()
    )
    status = "ROUTED" if ingest_ok and agents_ok else ("PARTIAL" if ingest_out.get("invoked") or agents_ok else "BLOCK")
    return UIResponse(
        status=status,
        text="ui→kernel→agents",
        mission_id=msg.session_id,
        detail={
            "ingest_ok": ingest_ok,
            "ingest_action": ingest_out.get("action"),
            "agents": agents,
            "llm_control": "DENY",
            "vendor_call": False,
        },
    )


class UIGatewayPlugin:
    def __init__(
        self,
        on_message: Callable[[UIMessage], UIResponse] | None = None,
        *,
        wire_kernel: bool = True,
    ):
        self.on_message = on_message
        self.wire_kernel = wire_kernel
        self.history: list[UIMessage] = []

    def handle(self, msg: UIMessage) -> UIResponse:
        self.history.append(msg)
        if self.on_message:
            return self.on_message(msg)
        if self.wire_kernel:
            return _route_kernel(msg)
        return UIResponse(
            status="ACK",
            text="Wordflow UI gateway ready — wire KernelLoopHook / continuous loop",
            detail={"session_id": msg.session_id, "received": msg.text[:200]},
        )

    def health(self) -> dict[str, Any]:
        return {
            "status": "OK",
            "plugin": "ui_gateway",
            "messages": len(self.history),
            "wire_kernel": self.wire_kernel,
        }
