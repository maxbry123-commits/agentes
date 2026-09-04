# -*- coding: utf-8 -*-
"""EvidencePacket normalizer — 0% LLM. A-AUD-01.
Rejects invalid packets with reason_codes. Does not trust claims.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SECRET_RE = re.compile(
    r"(token|api[_-]?key|password|bearer|ghp_|github_pat_)",
    re.IGNORECASE,
)
CLAIM_STATUS = frozenset({"COMPLETED", "PARTIAL", "FAILED"})

REASON = {
    "MISSING_PACKET": "MISSING_PACKET",
    "INVALID_PACKET_SCHEMA": "INVALID_PACKET_SCHEMA",
    "MISSING_FIELD": "MISSING_FIELD",
    "MISSING_DOC_ANCHOR": "MISSING_DOC_ANCHOR",
    "SECRET_IN_INPUT": "SECRET_IN_INPUT",
    "CI_MISSING": "CI_MISSING",
    "INVALID_COMMIT_SHA": "INVALID_COMMIT_SHA",
}


class PacketError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def _load_schema() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    path = root / "schema_module.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _require(obj: dict, key: str, path: str = "") -> Any:
    if key not in obj or obj[key] is None or obj[key] == "":
        raise PacketError(REASON["MISSING_FIELD"], f"{path}{key}")
    return obj[key]


def _check_sha(value: str, field: str) -> str:
    if not isinstance(value, str) or not SHA40.match(value):
        raise PacketError(REASON["INVALID_COMMIT_SHA"], field)
    return value


def _scan_secrets(obj: Any, path: str = "root") -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if SECRET_RE.search(str(k)):
                raise PacketError(REASON["SECRET_IN_INPUT"], f"key:{path}.{k}")
            _scan_secrets(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _scan_secrets(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        if SECRET_RE.search(obj) and "ci_url" not in path:
            if not obj.startswith("http"):
                raise PacketError(REASON["SECRET_IN_INPUT"], path)


def normalize_packet(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Validate and normalize EvidencePacket.

    Returns a cleaned dict with packet_hash.
    Raises PacketError with reason_code on failure.
    """
    if raw is None or not isinstance(raw, dict):
        raise PacketError(REASON["MISSING_PACKET"])

    _scan_secrets(raw)

    schema_version = _require(raw, "schema_version")
    if schema_version != "1.0":
        raise PacketError(
            REASON["INVALID_PACKET_SCHEMA"], f"schema_version={schema_version}"
        )

    task_id = str(_require(raw, "task_id"))
    claim_status = _require(raw, "claim_status")
    if claim_status not in CLAIM_STATUS:
        raise PacketError(
            REASON["INVALID_PACKET_SCHEMA"], f"claim_status={claim_status}"
        )

    repo = _require(raw, "repo")
    if not isinstance(repo, dict):
        raise PacketError(REASON["INVALID_PACKET_SCHEMA"], "repo")
    owner = str(_require(repo, "owner", "repo."))
    name = str(_require(repo, "name", "repo."))
    branch = str(_require(repo, "branch", "repo."))
    base_commit = _check_sha(str(_require(repo, "base_commit", "repo.")), "base_commit")
    final_commit = _check_sha(
        str(_require(repo, "final_commit", "repo.")), "final_commit"
    )

    files = _require(raw, "files")
    if not isinstance(files, dict):
        raise PacketError(REASON["INVALID_PACKET_SCHEMA"], "files")
    for key in ("added", "modified", "deleted"):
        if key not in files or not isinstance(files[key], list):
            raise PacketError(REASON["MISSING_FIELD"], f"files.{key}")

    doc_anchors = _require(raw, "doc_anchors")
    if not isinstance(doc_anchors, list) or len(doc_anchors) < 1:
        raise PacketError(REASON["MISSING_DOC_ANCHOR"])
    for i, a in enumerate(doc_anchors):
        if not isinstance(a, dict) or not a.get("doc_id"):
            raise PacketError(REASON["MISSING_DOC_ANCHOR"], f"doc_anchors[{i}]")

    tests = raw.get("tests") or {}
    if not isinstance(tests, dict):
        raise PacketError(REASON["INVALID_PACKET_SCHEMA"], "tests")
    claimed_passed = int(tests.get("claimed_passed") or 0)
    ci_run_id = tests.get("ci_run_id")
    ci_missing = claimed_passed > 0 and not ci_run_id

    packet: dict[str, Any] = {
        "schema_version": "1.0",
        "task_id": task_id,
        "block_id": raw.get("block_id"),
        "claim_status": claim_status,
        "repo": {
            "owner": owner,
            "name": name,
            "branch": branch,
            "base_commit": base_commit,
            "final_commit": final_commit,
        },
        "files": {
            "added": list(files["added"]),
            "modified": list(files["modified"]),
            "deleted": list(files["deleted"]),
        },
        "doc_anchors": list(doc_anchors),
        "tests": {
            "claimed_passed": claimed_passed,
            "claimed_total": int(tests.get("claimed_total") or 0),
            "ci_run_id": ci_run_id,
            "ci_url": tests.get("ci_url"),
        },
        "loc_claim": raw.get("loc_claim") or {},
        "blob_shas": raw.get("blob_shas") or {},
        "commands_run": raw.get("commands_run") or [],
        "meta": raw.get("meta") or {},
        "flags": {
            "ci_missing": ci_missing,
            "reason_ci": REASON["CI_MISSING"] if ci_missing else None,
        },
    }

    canonical = json.dumps(packet, sort_keys=True, separators=(",", ":"))
    packet["packet_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return packet


def validate_or_reason(raw: dict[str, Any] | None) -> tuple[bool, dict[str, Any]]:
    """Return (ok, packet_or_error). Never raises."""
    try:
        return True, normalize_packet(raw)
    except PacketError as e:
        return False, {"ok": False, "reason_code": e.reason_code, "detail": e.detail}
