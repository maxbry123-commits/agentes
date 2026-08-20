"""C7/S5 — puente dual evidence: engine dict + standards EvidencePacket."""
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
    change_id: str = "",
) -> Dict[str, Any]:
    eng = engine_packet or {}
    std = standards_packet.to_dict() if standards_packet else {}

    files = (eng.get("paths") or []) if isinstance(eng.get("paths"), list) else []
    file_paths = []
    for p in files:
        if isinstance(p, dict):
            file_paths.append(str(p.get("path", "")))
        else:
            file_paths.append(str(p))
    file_paths.extend(std.get("files_changed") or [])
    file_paths = [f for f in file_paths if f]

    mid = mission_id or std.get("mission_id") or eng.get("mission_id") or eng.get("notes") or "mission-local"
    tid = task_id or std.get("task_id") or eng.get("task_id") or "task-local"
    cid = change_id or std.get("change_id") or eng.get("change_id") or tid or "change-local"
    rev = revision or std.get("repository_revision") or eng.get("repository_revision") or "local"

    verdict = std.get("verdict") or eng.get("claim_status") or "PARTIAL"
    if verdict == "COMPLETED":
        verdict = "PASS"
    if verdict not in ("PASS", "FAIL", "PARTIAL"):
        verdict = "PARTIAL"

    packet = EvidencePacket(
        mission_id=str(mid)[:200],
        task_id=str(tid)[:200],
        change_id=str(cid)[:200],
        repository_revision=str(rev)[:200],
        files_changed=list(dict.fromkeys(file_paths)),
        tests=list(std.get("tests") or []) + (["engine_tests"] if eng.get("tests") else []),
        checks=list(std.get("checks") or []),
        artifacts=list(std.get("artifacts") or []),
        verdict=verdict,
        extra={"engine": eng, "standards": std},
    )
    return {
        "merged": packet.to_dict(),
        "complete": packet.is_complete(),
        "packet": packet,
    }
