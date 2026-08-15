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
