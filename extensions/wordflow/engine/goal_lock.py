# -*- coding: utf-8 -*-
"""GoalLock — C-01. Immutable mission contract after Sentinel PASS. 0% LLM."""
from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from typing import Any

from .goals_extractor import extract_goals_in
from .input_normalizer import InputBlockError, normalize_input_block
from .sentinel import run_sentinel


class GoalLockError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


class GoalLock:
    """Immutable after construction. Any mutation raises."""

    __slots__ = (
        "_locked", "lock_id", "block_id", "block_hash", "goals_in", "quality_bar",
        "priority", "constraints", "locked_at", "lock_hash", "source_type",
    )

    def __init__(self, payload: dict[str, Any]):
        object.__setattr__(self, "_locked", False)
        for k, v in payload.items():
            object.__setattr__(self, k, v)
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name: str, value: Any) -> None:
        if getattr(self, "_locked", False):
            raise GoalLockError("LOCK_IMMUTABLE", name)
        object.__setattr__(self, name, value)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lock_id": self.lock_id, "block_id": self.block_id, "block_hash": self.block_hash,
            "goals_in": self.goals_in, "quality_bar": self.quality_bar, "priority": self.priority,
            "constraints": self.constraints, "locked_at": self.locked_at, "lock_hash": self.lock_hash,
            "source_type": self.source_type,
        }


def _make_lock_hash(parts: dict[str, Any]) -> str:
    canonical = json.dumps(parts, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def lock_goals(raw: dict[str, Any] | None, *, strict_never_mvp: bool = True) -> dict[str, Any]:
    try:
        block = normalize_input_block(raw)
    except InputBlockError as e:
        return {"ok": False, "lock": None, "sentinel": None, "reason_codes": [e.reason_code], "detail": e.detail}
    goals_in = extract_goals_in(block)
    sentinel = run_sentinel(raw, goals_in=goals_in, strict_never_mvp=strict_never_mvp)
    if sentinel["verdict"] != "PASS":
        return {"ok": False, "lock": None, "sentinel": sentinel, "reason_codes": list(sentinel.get("reason_codes") or [])}
    block = sentinel.get("block") or block
    lock_id = f"GL-{block['block_id']}"
    locked_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    core = {
        "lock_id": lock_id, "block_id": block["block_id"], "block_hash": block["block_hash"],
        "goals_in": goals_in, "quality_bar": block["quality_bar"], "priority": block.get("priority", "P1"),
        "constraints": dict(block.get("constraints") or {}), "locked_at": locked_at,
        "source_type": block["source_type"],
    }
    core["lock_hash"] = _make_lock_hash({
        "lock_id": lock_id, "block_hash": core["block_hash"],
        "goals_in": {"covered_ids": goals_in.get("covered_ids"), "block_hash": goals_in.get("block_hash")},
        "quality_bar": core["quality_bar"],
    })
    gl = GoalLock(core)
    return {"ok": True, "lock": gl.to_dict(), "sentinel": sentinel, "reason_codes": []}


def admit_input(raw: dict[str, Any] | None) -> dict[str, Any]:
    try:
        return lock_goals(raw)
    except InputBlockError as e:
        return {"ok": False, "lock": None, "sentinel": None, "reason_codes": [e.reason_code], "detail": e.detail}


def create_goal_lock(goals: dict[str, Any]) -> dict[str, Any]:
    """Create the schema-compatible immutable GoalLock consumed by Engine ABI."""
    if not isinstance(goals, dict) or goals.get("status") != "COMPILED":
        raise GoalLockError("GOALS_NOT_COMPILED")
    data = dict(goals.get("goals") or {})
    objective = str(data.get("G01_objective") or "").strip()
    success = str(data.get("G05_success_criteria") or "").strip()
    if not objective or not success:
        raise GoalLockError("GOALS_REQUIRED_FIELDS_MISSING")
    lock = {
        "schema_version": "1.0",
        "lock_id": f"lock_{uuid.uuid4().hex[:12]}",
        "goals_id": str(goals.get("goals_id") or ""),
        "contract_id": str(goals.get("contract_id") or ""),
        "goals_hash": goals.get("goals_hash"),
        "form_hash": goals.get("form_hash"),
        "objective": objective,
        "success_criteria": success,
        "constraints": [str(x) for x in (data.get("G03_constraints") or [])],
        "forbidden": [str(x) for x in (data.get("G04_forbidden") or [])],
        "risk_level": str(data.get("G10_risk_level") or "unknown"),
        "approver": str(data.get("G12_approver") or "unknown"),
        "engines_allowed": [str(x) for x in (data.get("G09_engines_allowed") or [])],
        "status": "LOCKED",
        "locked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    lock["lock_hash"] = _make_lock_hash({k: v for k, v in lock.items() if k != "lock_hash"})
    return lock


def verify_lock_integrity(lock: dict[str, Any]) -> dict[str, Any]:
    """Verify the lock hash without modifying the lock."""
    if not isinstance(lock, dict):
        return {"ok": False, "reason": "LOCK_NOT_OBJECT"}
    expected = _make_lock_hash({k: v for k, v in lock.items() if k != "lock_hash"})
    actual = lock.get("lock_hash")
    ok = isinstance(actual, str) and actual == expected and lock.get("status") == "LOCKED"
    return {"ok": ok, "reason": "OK" if ok else "LOCK_HASH_MISMATCH", "expected": expected, "actual": actual}


def _tokens(text: str) -> set[str]:
    return {x for x in re.findall(r"[a-zA-Z0-9áéíóúüñ]{3,}", text.lower()) if x not in {"the", "and", "con", "para", "que", "los", "las", "una", "uno", "sin"}}


def validate_against_lock(lock: dict[str, Any], output_text: str) -> dict[str, Any]:
    """Deterministically gate engine output against objective and forbidden terms."""
    integrity = verify_lock_integrity(lock)
    if not integrity["ok"]:
        return {"ok": False, "action": "DISCARD_OUTPUT", "reason": "LOCK_INTEGRITY_FAILED", "violations": [integrity["reason"]]}
    text = str(output_text or "").strip()
    if not text:
        return {"ok": False, "action": "DISCARD_OUTPUT", "reason": "EMPTY_OUTPUT", "violations": ["EMPTY_OUTPUT"]}
    low = text.lower()
    forbidden = [str(x).strip() for x in (lock.get("forbidden") or []) if str(x).strip()]
    hits = [item for item in forbidden if item.lower() in low]
    if hits:
        return {"ok": False, "action": "DISCARD_OUTPUT", "reason": "FORBIDDEN_TERM", "violations": hits}
    objective_tokens = _tokens(str(lock.get("objective") or ""))
    output_tokens = _tokens(text)
    overlap = sorted(objective_tokens & output_tokens)
    if objective_tokens and not overlap:
        return {"ok": False, "action": "DISCARD_OUTPUT", "reason": "OBJECTIVE_MISMATCH", "violations": ["OBJECTIVE_MISMATCH"]}
    return {"ok": True, "action": "CONTINUE", "reason": "GOALS_ALIGNED", "violations": [], "objective_overlap": overlap}
