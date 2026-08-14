# -*- coding: utf-8 -*-
"""goals_out → EvidencePacket bridge — W2. 0% LLM. Aligns audit_forensic schema."""
from __future__ import annotations

from typing import Any


def goals_out_to_evidence_packet(
    *,
    block: dict[str, Any] | None,
    goals_out: dict[str, Any] | None,
    tasks: list[dict[str, Any]] | None = None,
    loop_status: str = "PARTIAL",
    repo: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build EvidencePacket-shaped dict from Wordflow loop state.

    Required keys match audit_forensic EvidencePacket v1:
    schema_version, task_id, claim_status, repo, files, doc_anchors.
    Missing repo commits use 40-zero placeholders (offline / no deploy yet).
    """
    block = block or {}
    goals_out = goals_out or {}
    tasks = tasks or []

    task_id = str(block.get("block_id") or "wordflow.unknown")
    claim = _map_claim_status(loop_status)

    doc_anchors = _doc_anchors_from_block(block)
    if not doc_anchors:
        doc_anchors = [{"doc_id": "wordflow.main_12", "path": "extensions/wordflow"}]

    files_added = [
        str(t.get("path")) for t in tasks if t.get("path") and t.get("status") != "DELETED"
    ]

    zero40 = "0" * 40
    repo_obj = {
        "owner": (repo or {}).get("owner", "maxbry123-commits"),
        "name": (repo or {}).get("name", "agentes"),
        "branch": (repo or {}).get("branch", "main"),
        "base_commit": (repo or {}).get("base_commit", zero40),
        "final_commit": (repo or {}).get("final_commit", zero40),
    }

    packet: dict[str, Any] = {
        "schema_version": "1.0",
        "task_id": task_id,
        "block_id": block.get("block_id"),
        "claim_status": claim,
        "repo": repo_obj,
        "files": {
            "added": files_added,
            "modified": [],
            "deleted": [],
        },
        "doc_anchors": doc_anchors,
        "meta": {
            "agent_id": "wordflow.main_12",
            "goals_out_done": [
                k for k, v in goals_out.items()
                if isinstance(v, dict) and v.get("status") == "DONE"
            ],
            "tasks_count": len(tasks),
        },
    }
    return packet


def _map_claim_status(loop_status: str) -> str:
    s = (loop_status or "").upper()
    if s == "COMPLETED":
        return "PARTIAL"  # loop done ≠ claim COMPLETED until W9 + tests
    if s in ("FAILED", "REJECTED"):
        return "FAILED"
    return "PARTIAL"


def _doc_anchors_from_block(block: dict[str, Any]) -> list[dict[str, Any]]:
    refs = block.get("doc_refs") or []
    out: list[dict[str, Any]] = []
    for r in refs:
        if isinstance(r, dict) and r.get("doc_id"):
            out.append({
                "doc_id": str(r["doc_id"]),
                "path": r.get("path"),
                "section": r.get("section"),
            })
        elif isinstance(r, str) and r:
            out.append({"doc_id": r})
    return out
