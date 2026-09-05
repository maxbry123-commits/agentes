"""T40 — Kimi/Minimax connection slot. PLACEHOLDER. No V1 fusion."""
from __future__ import annotations

import json
from pathlib import Path


def register_slot(registry: dict | None = None) -> dict:
    path = Path(__file__).with_name("kimi_minimax.ficha.v2.json")
    ficha = json.loads(path.read_text(encoding="utf-8"))
    if ficha.get("status") != "PLACEHOLDER":
        raise ValueError("slot must stay PLACEHOLDER in V1")
    if ficha.get("fusion"):
        raise ValueError("fusion forbidden in V1")
    dest = {} if registry is None else registry
    dest[ficha["artifact_id"]] = ficha
    return {"ok": True, "id": ficha["artifact_id"], "status": "PLACEHOLDER", "registry": dest}


if __name__ == "__main__":
    out = register_slot()
    assert out["status"] == "PLACEHOLDER"
    print("ok", out["id"], out["status"])
