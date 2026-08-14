# -*- coding: utf-8 -*-
"""GoalLock — T0e. Immutable goal outside LLM. 0% LLM."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any


class GoalLockError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hash_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _lock_body_for_hash(lock: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": lock["schema_version"],
        "lock_id": lock["lock_id"],
        "goals_id": lock["goals_id"],
        "contract_id": lock["contract_id"],
        "goals_hash": lock.get("goals_hash"),
        "form_hash": lock.get("form_hash"),
        "objective": lock["objective"],
        "success_criteria": lock["success_criteria"],
        "constraints": list(lock.get("constraints") or []),
        "forbidden": list(lock.get("forbidden") or []),
        "risk_level": lock.get("risk_level") or "unknown",
        "approver": lock.get("approver") or "unknown",
        "engines_allowed": list(lock.get("engines_allowed") or []),
        "status": lock["status"],
        "locked_at": lock["locked_at"],
    }


def create_goal_lock(goals_compiled: dict[str, Any], *,
                     lock_id: str | None = None) -> dict[str, Any]:
    """Create LOCKED GoalLock from COMPILED goals only."""
    if not isinstance(goals_compiled, dict):
        raise GoalLockError("INVALID_GOALS", "not a dict")
    if goals_compiled.get("status") != "COMPILED":
        raise GoalLockError(
            "GOALS_NOT_COMPILED",
            str(goals_compiled.get("status")),
        )
    g = goals_compiled.get("goals") or {}
    objective = (g.get("G01_objective") or "").strip()
    success = (g.get("G05_success_criteria") or "").strip()
    if not objective:
        raise GoalLockError("MISSING_OBJECTIVE")
    if not success:
        raise GoalLockError("MISSING_SUCCESS_CRITERIA")

    lock: dict[str, Any] = {
        "schema_version": "1.0",
        "lock_id": lock_id or f"gl_{uuid.uuid4().hex[:12]}",
        "goals_id": goals_compiled.get("goals_id") or "",
        "contract_id": goals_compiled.get("contract_id") or "",
        "goals_hash": goals_compiled.get("goals_hash"),
        "form_hash": goals_compiled.get("form_hash"),
        "objective": objective,
        "success_criteria": success,
        "constraints": list(g.get("G03_constraints") or []),
        "forbidden": list(g.get("G04_forbidden") or []),
        "risk_level": g.get("G10_risk_level") or "unknown",
        "approver": g.get("G12_approver") or "unknown",
        "engines_allowed": list(g.get("G09_engines_allowed") or []),
        "status": "LOCKED",
        "locked_at": _now(),
    }
    lock["lock_hash"] = _hash_payload(_lock_body_for_hash(lock))
    return lock


def verify_lock_integrity(lock: dict[str, Any]) -> dict[str, Any]:
    """Recompute hash; PASS only if matches and status LOCKED."""
    if not isinstance(lock, dict):
        return {"ok": False, "reason": "INVALID_LOCK"}
    if lock.get("status") != "LOCKED":
        return {"ok": False, "reason": "NOT_LOCKED", "status": lock.get("status")}
    expected = _hash_payload(_lock_body_for_hash(lock))
    actual = lock.get("lock_hash")
    if actual != expected:
        return {"ok": False, "reason": "HASH_MISMATCH", "expected": expected, "actual": actual}
    return {"ok": True, "reason": "INTEGRITY_OK", "lock_id": lock.get("lock_id")}


def validate_against_lock(lock: dict[str, Any], output_text: str) -> dict[str, Any]:
    """Discard engine/LLM output if it violates forbidden or drops objective signal.

    Deterministic checks only (substring). No LLM.
    """
    integ = verify_lock_integrity(lock)
    if not integ["ok"]:
        return {"ok": False, "reason": "LOCK_INTEGRITY_FAIL", "detail": integ}

    text = (output_text or "").lower()
    obj = (lock.get("objective") or "").lower()
    violations: list[str] = []

    for term in lock.get("forbidden") or []:
        t = str(term).strip().lower()
        if t and t in text:
            violations.append(f"forbidden:{term}")

    # Soft objective echo: require at least one significant token from objective
    tokens = [w for w in obj.replace(",", " ").split() if len(w) > 4]
    if tokens and not any(tok in text for tok in tokens[:5]):
        violations.append("objective_not_reflected")

    if violations:
        return {
            "ok": False,
            "reason": "GOAL_VIOLATION",
            "violations": violations,
            "action": "DISCARD_OUTPUT",
            "lock_id": lock.get("lock_id"),
        }
    return {
        "ok": True,
        "reason": "GOAL_ALIGNED",
        "action": "ACCEPT",
        "lock_id": lock.get("lock_id"),
    }


def release_lock(lock: dict[str, Any], *,
                 reason: str = "explicit_release") -> dict[str, Any]:
    """Explicit release only — does not mutate original; returns new object."""
    integ = verify_lock_integrity(lock)
    if not integ["ok"] and lock.get("status") == "LOCKED":
        raise GoalLockError("CANNOT_RELEASE_CORRUPT", str(integ))
    out = dict(lock)
    out["status"] = "RELEASED"
    out["release_reason"] = reason
    # status change → new hash not required for RELEASED verification path
    return out
