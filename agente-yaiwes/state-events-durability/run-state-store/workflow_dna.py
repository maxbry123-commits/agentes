# -*- coding: utf-8 -*-
"""WorkflowDNA — T36. Immutable execution plan fingerprint. 0% LLM."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .goal_lock import verify_lock_integrity


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _body(dna: dict[str, Any]) -> dict[str, Any]:
    return {
        "dna_id": dna["dna_id"],
        "lock_id": dna["lock_id"],
        "workflow_version": dna.get("workflow_version"),
        "objectives": dna.get("objectives") or [],
        "dag_digest": dna.get("dag_digest"),
        "policies": dna.get("policies") or {},
        "success_criteria": dna.get("success_criteria") or [],
        "rollback": dna.get("rollback") or {},
        "created_at": dna["created_at"],
    }


def _hash(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compile_dna(
    lock: dict[str, Any],
    *,
    workflow_version: str = "1.0",
    objectives: list[Any] | None = None,
    dag_digest: str | None = None,
    policies: dict[str, Any] | None = None,
    success_criteria: list[Any] | None = None,
    rollback: dict[str, Any] | None = None,
) -> dict[str, Any]:
    integ = verify_lock_integrity(lock)
    if not integ.get("ok"):
        raise ValueError(f"lock integrity failed: {integ}")

    dna: dict[str, Any] = {
        "dna_id": f"dna_{uuid.uuid4().hex[:12]}",
        "lock_id": lock["lock_id"],
        "workflow_version": workflow_version,
        "objectives": list(objectives or lock.get("objectives") or []),
        "dag_digest": dag_digest,
        "policies": dict(policies or {}),
        "success_criteria": list(success_criteria or []),
        "rollback": dict(rollback or {}),
        "created_at": _now(),
    }
    dna["dna_hash"] = _hash(_body(dna))
    return dna


def verify_dna(dna: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(dna, dict) or "dna_hash" not in dna:
        return {"ok": False, "reason": "INVALID"}
    expected = _hash(_body(dna))
    if dna.get("dna_hash") != expected:
        return {"ok": False, "reason": "HASH_MISMATCH"}
    return {"ok": True, "reason": "DNA_OK", "dna_id": dna.get("dna_id")}
