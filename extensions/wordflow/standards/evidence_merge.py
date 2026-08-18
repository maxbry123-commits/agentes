"""C7 — puente dual evidence: engine packet (dict) + standards EvidencePacket."""
from __future__ import annotations
from typing import Any, Dict, Optional
from .evidence import EvidencePacket


def merge_evidence(
    *,
    engine_packet: Optional[Dict[str, Any]] = None,
    standards_packet: Optional[EvidencePacket] = None,
    mission_id: str = "",
    task_id: str = "",
    revision: str = "",
) -> Dict[str, Any]:
    eng = engine_packet or {}
    std = standards_packet.to_dict() if standards_packet else {}
    files = list(dict.fromkeys((eng.get("paths") or []) if isinstance(eng.get("paths"), list) else []))
    # engine paths often list of dicts
    file_paths = []
    for p in files:
        if isinstance(p, dict):
            file_paths.append(str(p.get("path", "")))
        else:
            file_paths.append(str(p))
    file_paths.extend(std.get("files_changed") or [])
    file_paths = [f for f in file_paths if f]

    verdict = std.get("verdict") or eng.get("claim_status") or "PARTIAL"
    if verdict == "COMPLETED":
        verdict = "PASS"
    packet = EvidencePacket(
        mission_id=mission_id or std.get("mission_id") or eng.get("mission_id") or "",
        task_id=task_id or std.get("task_id") or eng.get("task_id") or "",
        change_id=std.get("change_id") or eng.get("change_id") or eng.get("task_id") or "",
        repository_revision=revision or std.get("repository_revision") or "local",
        files_changed=list(dict.fromkeys(file_paths)),
        tests=list(std.get("tests") or []) + (["engine_tests"] if eng.get("tests") else []),
        checks=list(std.get("checks") or []),
        artifacts=list(std.get("artifacts") or []),
        verdict=verdict if verdict in ("PASS", "FAIL", "PARTIAL") else "PARTIAL",
        extra={"engine": eng, "standards": std},
    )
    return {
        "merged": packet.to_dict(),
        "complete": packet.is_complete(),
        "packet": packet,
    }
