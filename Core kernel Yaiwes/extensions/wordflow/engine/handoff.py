# -*- coding: utf-8 -*-
"""Handoff Package — T6. Compile/validate portable context. 0% LLM."""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from .goal_lock import verify_lock_integrity


def _hash(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _body_for_hash(h: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": h["schema_version"],
        "handoff_id": h["handoff_id"],
        "lock_id": h["lock_id"],
        "lock_hash": h.get("lock_hash"),
        "goal": h["goal"],
        "success_criteria": h.get("success_criteria"),
        "constraints": list(h.get("constraints") or []),
        "forbidden": list(h.get("forbidden") or []),
        "artifacts": list(h.get("artifacts") or []),
        "evidence": list(h.get("evidence") or []),
        "checkpoint_id": h.get("checkpoint_id"),
        "next_step": h.get("next_step"),
        "registers_snapshot": h.get("registers_snapshot"),
        "manifest_id": h.get("manifest_id"),
        "status": h["status"],
    }


def compile_handoff(
    lock: dict[str, Any],
    *,
    artifacts: list[str] | None = None,
    evidence: list[str] | None = None,
    checkpoint_id: str | None = None,
    next_step: str | None = None,
    registers_file: dict[str, Any] | None = None,
    manifest_id: str | None = None,
    status: str = "READY",
    require_lock_intact: bool = True,
) -> dict[str, Any]:
    if require_lock_intact:
        integ = verify_lock_integrity(lock)
        if not integ["ok"]:
            raise ValueError(f"lock not intact: {integ.get('reason')}")
    if status not in ("READY", "IN_PROGRESS", "BLOCKED", "DONE"):
        raise ValueError(f"invalid status={status}")

    regs_snap = None
    if registers_file is not None:
        regs_snap = dict(registers_file.get("registers") or {})

    body: dict[str, Any] = {
        "schema_version": "1.0",
        "handoff_id": f"ho_{uuid.uuid4().hex[:12]}",
        "lock_id": lock.get("lock_id") or "",
        "lock_hash": lock.get("lock_hash"),
        "goal": lock.get("objective") or "",
        "success_criteria": lock.get("success_criteria"),
        "constraints": list(lock.get("constraints") or []),
        "forbidden": list(lock.get("forbidden") or []),
        "artifacts": [str(a) for a in (artifacts or [])],
        "evidence": [str(e) for e in (evidence or [])],
        "checkpoint_id": checkpoint_id,
        "next_step": next_step,
        "registers_snapshot": regs_snap,
        "manifest_id": manifest_id,
        "status": status,
    }
    body["handoff_hash"] = _hash(_body_for_hash(body))
    return body


def validate_handoff(package: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(package, dict):
        return {"ok": False, "reason": "INVALID_PACKAGE"}
    for key in ("handoff_id", "lock_id", "goal", "status", "handoff_hash"):
        if not package.get(key):
            return {"ok": False, "reason": f"MISSING_{key.upper()}"}
    if package.get("status") not in ("READY", "IN_PROGRESS", "BLOCKED", "DONE"):
        return {"ok": False, "reason": "INVALID_STATUS"}
    expected = _hash(_body_for_hash(package))
    if package.get("handoff_hash") != expected:
        return {"ok": False, "reason": "HASH_MISMATCH", "expected": expected}
    return {"ok": True, "reason": "HANDOFF_OK", "handoff_id": package.get("handoff_id")}
