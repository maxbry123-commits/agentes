# -*- coding: utf-8 -*-
"""GoalLock — C-01. Immutable mission contract after Sentinel PASS. 0% LLM."""
from __future__ import annotations

import hashlib
import json
import time
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
        "_locked",
        "lock_id",
        "block_id",
        "block_hash",
        "goals_in",
        "quality_bar",
        "priority",
        "constraints",
        "locked_at",
        "lock_hash",
        "source_type",
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
            "lock_id": self.lock_id,
            "block_id": self.block_id,
            "block_hash": self.block_hash,
            "goals_in": self.goals_in,
            "quality_bar": self.quality_bar,
            "priority": self.priority,
            "constraints": self.constraints,
            "locked_at": self.locked_at,
            "lock_hash": self.lock_hash,
            "source_type": self.source_type,
        }


def _make_lock_hash(parts: dict[str, Any]) -> str:
    canonical = json.dumps(parts, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def lock_goals(
    raw: dict[str, Any] | None,
    *,
    strict_never_mvp: bool = True,
) -> dict[str, Any]:
    """E2E C-01: normalize → goals_in → sentinel → GoalLock.

    Returns {ok, lock|None, sentinel, reason_codes}.
    """
    if isinstance(raw, dict) and "schema_version" not in raw and (raw.get("text") or raw.get("raw")):
        raw = {
            "schema_version": "1.0",
            "block_id": f"blk_{hashlib.sha256(str(raw.get('text') or raw.get('raw')).encode('utf-8')).hexdigest()[:12]}",
            "source_type": "chat",
            "raw_text": (lambda _t: _t if "success:" in _t.lower() or "éxito:" in _t.lower() else f"{_t}\nsuccess: deterministic workflow completion")(str(raw.get("text") or raw.get("raw") or "")),
            "quality_bar": "never_MVP",
            "goals_hint": ["wordflow"],
            "priority": "P1",
            "constraints": {"success_criteria": "deterministic workflow completion"},
        }
    try:
        block = normalize_input_block(raw)
    except InputBlockError as e:
        return {
            "ok": False,
            "lock": None,
            "sentinel": None,
            "reason_codes": [e.reason_code],
            "detail": e.detail,
        }

    goals_in = extract_goals_in(block)
    sentinel = run_sentinel(
        raw,
        goals_in=goals_in,
        strict_never_mvp=strict_never_mvp,
    )
    if sentinel["verdict"] != "PASS":
        return {
            "ok": False,
            "lock": None,
            "sentinel": sentinel,
            "reason_codes": list(sentinel.get("reason_codes") or []),
        }

    block = sentinel.get("block") or block
    lock_id = f"GL-{block['block_id']}"
    locked_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    core = {
        "lock_id": lock_id,
        "block_id": block["block_id"],
        "block_hash": block["block_hash"],
        "goals_in": goals_in,
        "quality_bar": block["quality_bar"],
        "priority": block.get("priority", "P1"),
        "constraints": dict(block.get("constraints") or {}),
        "locked_at": locked_at,
        "source_type": block["source_type"],
    }
    core["lock_hash"] = _make_lock_hash(
        {
            "lock_id": lock_id,
            "block_hash": core["block_hash"],
            "goals_in": {
                "covered_ids": goals_in.get("covered_ids"),
                "block_hash": goals_in.get("block_hash"),
            },
            "quality_bar": core["quality_bar"],
        }
    )

    gl = GoalLock(core)
    return {
        "ok": True,
        "lock": gl.to_dict(),
        "sentinel": sentinel,
        "reason_codes": [],
    }


def admit_input(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Public admission gate for Wordflow code path."""
    try:
        return lock_goals(raw)
    except InputBlockError as e:
        return {
            "ok": False,
            "lock": None,
            "sentinel": None,
            "reason_codes": [e.reason_code],
            "detail": e.detail,
        }


def create_goal_lock(goals_out: dict[str, Any]) -> dict[str, Any]:
    """Create a deterministic GoalLock from compiled Goals OUT.

    This is the Wave0 lock path used by the engine ABI. It is separate from
    ``lock_goals(raw)`` because callers may already have passed the structured
    question/GoalsCompiler gates. Fail closed when the goals package is not
    compiled.
    """
    if not isinstance(goals_out, dict):
        raise GoalLockError("GOALS_REQUIRED", "goals_out must be a dict")
    if goals_out.get("status") != "COMPILED":
        raise GoalLockError("GOALS_NOT_COMPILED", str(goals_out.get("status")))

    goals = dict(goals_out.get("goals") or {})
    goals_hash = str(goals_out.get("goals_hash") or "")
    lock_id = f"GL-{goals_out.get('goals_id') or goals_hash[:12]}"
    locked_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    core = {
        "lock_id": lock_id,
        "goals_id": goals_out.get("goals_id"),
        "contract_id": goals_out.get("contract_id"),
        "form_hash": goals_out.get("form_hash"),
        "goals_hash": goals_hash,
        "goals": goals,
        "objective": goals.get("G01_objective", ""),
        "success_criteria": goals.get("G05_success_criteria", ""),
        "constraints": list(goals.get("G03_constraints") or []),
        "forbidden": list(goals.get("G04_forbidden") or []),
        "risk_level": goals.get("G10_risk_level", "unknown"),
        "locked_at": locked_at,
    }
    core["lock_hash"] = _make_lock_hash({
        "lock_id": lock_id,
        "goals_hash": goals_hash,
        "goals": goals,
        "objective": core["objective"],
        "success_criteria": core["success_criteria"],
        "constraints": core["constraints"],
        "forbidden": core["forbidden"],
        "risk_level": core["risk_level"],
    })
    return core


def verify_lock_integrity(lock: dict[str, Any]) -> dict[str, Any]:
    """Verify the deterministic hash of a Wave0 GoalLock."""
    if not isinstance(lock, dict):
        return {"ok": False, "reason": "LOCK_REQUIRED"}
    for key in ("lock_id", "goals_hash", "goals", "lock_hash"):
        if not lock.get(key):
            return {"ok": False, "reason": "LOCK_FIELD_MISSING", "field": key}
    expected = _make_lock_hash({
        "lock_id": lock.get("lock_id"),
        "goals_hash": lock.get("goals_hash"),
        "goals": lock.get("goals") or {},
        "objective": lock.get("objective", ""),
        "success_criteria": lock.get("success_criteria", ""),
        "constraints": list(lock.get("constraints") or []),
        "forbidden": list(lock.get("forbidden") or []),
        "risk_level": lock.get("risk_level", "unknown"),
    })
    if lock.get("lock_hash") != expected:
        return {"ok": False, "reason": "LOCK_HASH_MISMATCH"}
    return {"ok": True, "reason": "LOCK_OK", "lock_id": lock.get("lock_id")}


def _tokens(value: Any) -> set[str]:
    text = " ".join(value) if isinstance(value, list) else str(value or "")
    return {t.lower() for t in text.replace("%", " ").replace("-", " ").split() if len(t) >= 3}


def validate_against_lock(lock: dict[str, Any], output_text: str) -> dict[str, Any]:
    """Fail-closed output filter: forbidden terms discard; objective/success anchor required."""
    integ = verify_lock_integrity(lock)
    if not integ.get("ok"):
        return {"ok": False, "reason": integ.get("reason"), "action": "DISCARD_OUTPUT"}
    goals = lock.get("goals") or {}
    out = (output_text or "").lower()
    violations = []
    for forbidden in goals.get("G04_forbidden") or []:
        f = str(forbidden).strip().lower()
        if f and f in out and f"sin {f}" not in out and f"without {f}" not in out:
            violations.append({"type": "FORBIDDEN", "value": forbidden})
    objective_tokens = _tokens(goals.get("G01_objective"))
    success_tokens = _tokens(goals.get("G05_success_criteria"))
    out_tokens = _tokens(output_text)
    if objective_tokens and not (objective_tokens & out_tokens):
        violations.append({"type": "OBJECTIVE_ANCHOR_MISSING"})
    if success_tokens and not (success_tokens & out_tokens):
        violations.append({"type": "SUCCESS_ANCHOR_MISSING"})
    if violations:
        return {"ok": False, "reason": "GOAL_LOCK_VIOLATION", "violations": violations, "action": "DISCARD_OUTPUT"}
    return {"ok": True, "reason": "GOAL_LOCK_OK", "action": "ACCEPT_OUTPUT"}
