# -*- coding: utf-8 -*-
"""C-07 EvidencePacket — formal claim-ready evidence unit. 0% LLM."""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any

CLAIM_STATUS = frozenset({"PARTIAL", "COMPLETED", "REFUTADO"})


class EvidencePacketError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _sha(obj: Any) -> str:
    return hashlib.sha256(_canonical(obj).encode("utf-8")).hexdigest()


def build_evidence_packet(
    *,
    task_id: str,
    claim_status: str = "PARTIAL",
    paths: list[dict[str, Any]] | None = None,
    tests: dict[str, Any] | None = None,
    doc_anchors: list[str] | None = None,
    commit_sha: str | None = None,
    notes: str = "",
    parent_hash: str | None = None,
    timestamp: float | None = None,
) -> dict[str, Any]:
    if not task_id:
        raise EvidencePacketError("TASK_ID_EMPTY")
    if claim_status not in CLAIM_STATUS:
        raise EvidencePacketError("BAD_CLAIM_STATUS", claim_status)

    body = {
        "schema_version": "1.0",
        "task_id": task_id,
        "claim_status": claim_status,
        "paths": list(paths or []),
        "tests": dict(tests or {}),
        "doc_anchors": list(doc_anchors or []),
        "commit_sha": commit_sha,
        "notes": notes,
        "parent_hash": parent_hash,
        "ts": time.time() if timestamp is None else timestamp,
        "llm_control": "DENY",
    }
    body["packet_hash"] = _sha({k: v for k, v in body.items() if k != "packet_hash"})
    return body


def verify_evidence_packet(packet: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(packet, dict):
        return {"ok": False, "reason": "NOT_OBJECT"}
    expected = _sha({k: v for k, v in packet.items() if k != "packet_hash"})
    if packet.get("packet_hash") != expected:
        return {"ok": False, "reason": "HASH_MISMATCH"}
    if packet.get("claim_status") not in CLAIM_STATUS:
        return {"ok": False, "reason": "BAD_CLAIM_STATUS"}
    if not packet.get("task_id"):
        return {"ok": False, "reason": "TASK_ID_EMPTY"}
    return {"ok": True, "task_id": packet["task_id"], "packet_hash": packet["packet_hash"]}


def chain_packets(packets: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate source packets, then create a deterministic parent-hash chain."""
    if not packets:
        raise EvidencePacketError("NO_PACKETS")
    out: list[dict[str, Any]] = []
    prev = None
    for source in packets:
        verified = verify_evidence_packet(source)
        if not verified["ok"]:
            raise EvidencePacketError("INVALID_SOURCE_PACKET", verified["reason"])
        rebuilt = build_evidence_packet(
            task_id=str(source["task_id"]),
            claim_status=str(source["claim_status"]),
            paths=list(source.get("paths") or []),
            tests=dict(source.get("tests") or {}),
            doc_anchors=list(source.get("doc_anchors") or []),
            commit_sha=source.get("commit_sha"),
            notes=str(source.get("notes") or ""),
            parent_hash=prev,
            timestamp=float(source["ts"]),
        )
        out.append(rebuilt)
        prev = rebuilt["packet_hash"]
    return {
        "ok": True,
        "count": len(out),
        "tip_hash": out[-1]["packet_hash"],
        "packets": out,
        "llm_control": "DENY",
    }


def verify_packet_chain(packets: list[dict[str, Any]]) -> dict[str, Any]:
    """Verify packet hashes and parent links without rebuilding or mutating them."""
    if not packets:
        return {"ok": False, "reason": "NO_PACKETS"}
    previous = None
    for index, packet in enumerate(packets, start=1):
        verified = verify_evidence_packet(packet)
        if not verified["ok"]:
            return {"ok": False, "reason": verified["reason"], "index": index}
        if packet.get("parent_hash") != previous:
            return {"ok": False, "reason": "PARENT_HASH_MISMATCH", "index": index}
        previous = packet["packet_hash"]
    return {"ok": True, "count": len(packets), "tip_hash": previous, "llm_control": "DENY"}
