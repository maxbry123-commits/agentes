# -*- coding: utf-8 -*-
"""C-24 Ledger — append-only historical record (not live Blackboard). 0% LLM."""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any


class LedgerError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def _entry_hash(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class Ledger:
    """Immutable history. No update/delete of past entries."""

    def __init__(self, mission_id: str = ""):
        self.mission_id = mission_id
        self._entries: list[dict[str, Any]] = []

    def append(self, kind: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not kind:
            raise LedgerError("KIND_EMPTY")
        prev = self._entries[-1]["entry_hash"] if self._entries else None
        body = {
            "seq": len(self._entries),
            "kind": kind,
            "payload": dict(payload or {}),
            "mission_id": self.mission_id,
            "ts": time.time(),
            "prev_hash": prev,
            "llm_control": "DENY",
        }
        body["entry_hash"] = _entry_hash({k: v for k, v in body.items() if k != "entry_hash"})
        self._entries.append(body)
        return body

    def entries(self) -> list[dict[str, Any]]:
        return list(self._entries)

    def tip_hash(self) -> str | None:
        if not self._entries:
            return None
        return self._entries[-1]["entry_hash"]

    def verify_chain(self) -> dict[str, Any]:
        prev = None
        for i, e in enumerate(self._entries):
            if e.get("prev_hash") != prev:
                return {"ok": False, "reason": "CHAIN_BREAK", "seq": i}
            expected = _entry_hash({k: v for k, v in e.items() if k != "entry_hash"})
            if e.get("entry_hash") != expected:
                return {"ok": False, "reason": "HASH_MISMATCH", "seq": i}
            prev = e["entry_hash"]
        return {"ok": True, "count": len(self._entries), "tip": self.tip_hash()}
