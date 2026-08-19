"""T34 — write_evidence(path_result). Packet with timestamp + instance_id. No V1 claim."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def write_evidence(path_result: dict[str, Any], dest: Path | None = None) -> dict[str, Any]:
    instance_id = str((path_result or {}).get("instance_id") or "v1")
    packet = {
        "ok": True,
        "instance_id": instance_id,
        "timestamp": time.time(),
        "path_result": dict(path_result or {}),
        "claim_v1": False,
    }
    if dest is not None:
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(packet, ensure_ascii=False, default=str), encoding="utf-8")
        packet["path"] = str(dest)
    return packet


if __name__ == "__main__":
    import tempfile

    pkt = write_evidence({"instance_id": "v1", "status": "ok"})
    assert pkt["instance_id"] == "v1" and "timestamp" in pkt
    assert pkt["claim_v1"] is False
    with tempfile.TemporaryDirectory() as tmp:
        out = write_evidence({"instance_id": "v2"}, dest=Path(tmp) / "e.json")
        assert Path(out["path"]).is_file()
    print("ok", pkt["instance_id"], bool(pkt["timestamp"]))
