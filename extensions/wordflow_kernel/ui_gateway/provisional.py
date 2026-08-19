"""Provisional UI facade — one-shot, no server, no vendor.

Usage:
  python -m wordflow_kernel.ui_gateway.provisional "objective: ping kernel"
"""
from __future__ import annotations

import json
import sys

from .plugin import UIGatewayPlugin, UIMessage


def run(text: str, session_id: str = "ui-provisional") -> dict:
    plugin = UIGatewayPlugin(wire_kernel=True)
    resp = plugin.handle(UIMessage(session_id=session_id, text=text))
    return {
        "status": resp.status,
        "text": resp.text,
        "mission_id": resp.mission_id,
        "detail": resp.detail,
        "health": plugin.health(),
        "llm_control": "DENY",
    }


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    text = " ".join(args) or "objective: provisional ui ping\nsuccess: kernel routed"
    out = run(text)
    print(json.dumps(out, indent=2, default=str))
    return 0 if out.get("status") in ("ROUTED", "PARTIAL", "ACK") else 1


if __name__ == "__main__":
    raise SystemExit(main())
