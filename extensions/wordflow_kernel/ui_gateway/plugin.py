"""UI Gateway Plugin — connect Wordflow/YAIWES to webui/chat/OpenClaw UI.

Stub: accepts messages, returns structured plan status. Does not embed UI.
Real OpenClaw UI host mounts this via enchufe ficha.
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


class UIGatewayPlugin:
    def __init__(self, on_message: Callable[[UIMessage], UIResponse] | None = None):
        self.on_message = on_message
        self.history: list[UIMessage] = []

    def handle(self, msg: UIMessage) -> UIResponse:
        self.history.append(msg)
        if self.on_message:
            return self.on_message(msg)
        return UIResponse(
            status="ACK",
            text="Wordflow UI gateway ready — wire KernelLoopHook / continuous loop",
            detail={"session_id": msg.session_id, "received": msg.text[:200]},
        )

    def health(self) -> dict[str, Any]:
        return {"status": "OK", "plugin": "ui_gateway", "messages": len(self.history)}
