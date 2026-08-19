"""T21 — handle_message(msg) ping/echo/status/convert. No chat LLM."""
from __future__ import annotations

from typing import Any


def handle_message(msg: dict) -> dict[str, Any]:
    if not isinstance(msg, dict):
        return {
            "ok": False,
            "action": "error",
            "payload": {"code": "INVALID_MSG", "detail": "msg must be dict"},
        }
    action = msg.get("action") or msg.get("type") or msg.get("cmd")
    if action == "ping":
        return {"ok": True, "action": "pong", "payload": msg.get("payload")}
    if action == "echo":
        return {"ok": True, "action": "echo", "payload": msg.get("payload")}
    if action == "status":
        return {"ok": True, "action": "status", "payload": {"alive": True}}
    if action in ("convert", "reception", "ingest"):
        from .reception.convert import ingest, locate

        if action == "reception" and (msg.get("payload") or {}).get("locate"):
            return {"ok": True, "action": "reception", "payload": locate()}
        block = msg.get("payload") or msg.get("input_block") or {}
        if not isinstance(block, dict):
            block = {"raw_text": str(block)}
        out = ingest(
            block,
            use_sdpa=bool(msg.get("use_sdpa")),
            branch=str(msg.get("branch") or "default"),
        )
        return {"ok": out["ok"], "action": action, "payload": out}
    return {
        "ok": False,
        "action": "error",
        "payload": {"code": "UNKNOWN_ACTION", "got": action},
    }


if __name__ == "__main__":
    out = handle_message({"action": "ping"})
    assert out["ok"] is True and out["action"] == "pong"
    echo = handle_message({"action": "echo", "payload": "hi"})
    assert echo["payload"] == "hi"
    err = handle_message({"action": "chat"})
    assert err["ok"] is False and err["payload"]["code"] == "UNKNOWN_ACTION"
    rec = handle_message({"action": "reception", "payload": {"locate": True}})
    assert rec["ok"] is True
    print("ok", out["action"], echo["payload"], err["payload"]["code"], rec["action"])
