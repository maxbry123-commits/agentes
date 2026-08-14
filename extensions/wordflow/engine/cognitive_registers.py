# -*- coding: utf-8 -*-
"""Cognitive Register File — T0j. R0-R15 load/store. 0% LLM."""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from .goal_lock import verify_lock_integrity

REGISTER_KEYS = (
    "R0_objective",
    "R1_step",
    "R2_success",
    "R3_constraints",
    "R4_risks",
    "R5_resources",
    "R6_tools",
    "R7_state",
    "R8_checkpoint",
    "R9_evidence",
    "R10_hypothesis",
    "R11_refutation",
    "R12_next",
    "R13_quality",
    "R14_confidence",
    "R15_exit_condition",
)

LIST_REGS = {"R3_constraints", "R5_resources", "R6_tools", "R9_evidence"}


def _hash(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _empty_registers() -> dict[str, Any]:
    regs: dict[str, Any] = {}
    for k in REGISTER_KEYS:
        regs[k] = [] if k in LIST_REGS else None
    return regs


def load_from_lock(lock: dict[str, Any], *,
                   file_id: str | None = None) -> dict[str, Any]:
    """Seed registers from GoalLock. R0/R2/R3/R4 from lock; rest empty."""
    integ = verify_lock_integrity(lock)
    if not integ["ok"]:
        raise ValueError(f"lock integrity fail: {integ.get('reason')}")

    regs = _empty_registers()
    regs["R0_objective"] = lock.get("objective")
    regs["R2_success"] = lock.get("success_criteria")
    regs["R3_constraints"] = list(lock.get("constraints") or [])
    regs["R4_risks"] = lock.get("risk_level")
    regs["R15_exit_condition"] = lock.get("success_criteria")

    body: dict[str, Any] = {
        "schema_version": "1.0",
        "file_id": file_id or f"crf_{uuid.uuid4().hex[:12]}",
        "lock_id": lock.get("lock_id") or "",
        "registers": regs,
    }
    body["file_hash"] = _hash({k: v for k, v in body.items() if k != "file_hash"})
    return body


def set_register(file: dict[str, Any], key: str, value: Any) -> dict[str, Any]:
    """Set one register; return new file object (copy). R0 cannot diverge from lock objective once set from lock — caller must not overwrite R0 with foreign goal."""
    if key not in REGISTER_KEYS:
        raise KeyError(f"unknown register {key}")
    if key in LIST_REGS and value is not None and not isinstance(value, list):
        raise TypeError(f"{key} expects list")
    if key == "R14_confidence" and value is not None:
        if not isinstance(value, (int, float)) or value < 0 or value > 1:
            raise ValueError("R14_confidence must be 0..1")

    out = {
        "schema_version": "1.0",
        "file_id": file["file_id"],
        "lock_id": file["lock_id"],
        "registers": dict(file.get("registers") or {}),
    }
    out["registers"][key] = value
    # ensure all keys present
    for k in REGISTER_KEYS:
        out["registers"].setdefault(k, [] if k in LIST_REGS else None)
    out["file_hash"] = _hash({k: v for k, v in out.items() if k != "file_hash"})
    return out


def as_prompt_block(file: dict[str, Any]) -> str:
    """Serialize registers for engine injection."""
    regs = file.get("registers") or {}
    lines = ["=== COGNITIVE_REGISTERS ===", f"file_id: {file.get('file_id')}", f"lock_id: {file.get('lock_id')}"]
    for k in REGISTER_KEYS:
        v = regs.get(k)
        if v is None or v == []:
            continue
        if isinstance(v, list):
            lines.append(f"{k}:")
            lines.extend(f"  - {item}" for item in v)
        else:
            lines.append(f"{k}: {v}")
    lines.append("=== END REGISTERS ===")
    return "\n".join(lines)


def merge_memory_pack(file: dict[str, Any], pack: dict[str, Any]) -> dict[str, Any]:
    """Merge MemoryPack-like dict into R5/R7/R8/R9 without touching R0."""
    out = file
    facts = list(pack.get("facts") or [])
    open_loops = list(pack.get("open_loops") or [])
    constraints_echo = list(pack.get("constraints_echo") or [])
    if facts:
        prev = list((out.get("registers") or {}).get("R9_evidence") or [])
        out = set_register(out, "R9_evidence", prev + [str(f) for f in facts])
    if open_loops:
        out = set_register(out, "R12_next", "; ".join(str(x) for x in open_loops))
    if pack.get("checkpoint_ref"):
        out = set_register(out, "R8_checkpoint", str(pack["checkpoint_ref"]))
    if constraints_echo:
        prev_c = list((out.get("registers") or {}).get("R3_constraints") or [])
        merged = prev_c + [c for c in constraints_echo if c not in prev_c]
        out = set_register(out, "R3_constraints", merged)
    if pack.get("state"):
        out = set_register(out, "R7_state", str(pack["state"]))
    return out
