# -*- coding: utf-8 -*-
"""Bitácora / EventStore — T0h. Append-only work journal. 0% LLM."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

GENESIS_PREV = "0" * 64
ALLOWED_KINDS = frozenset(
    {"LOCK_CREATED", "PING", "FOCUS", "STEP", "TOOL", "GATE", "REPLAN", "NOTE", "ERROR"}
)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hash(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _event_body_for_hash(ev: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": ev["schema_version"],
        "event_id": ev["event_id"],
        "seq": ev["seq"],
        "ts": ev["ts"],
        "kind": ev["kind"],
        "lock_id": ev["lock_id"],
        "payload": ev.get("payload") or {},
        "prev_hash": ev["prev_hash"],
    }


class BitacoraStore:
    """In-memory append-only log with optional JSONL persistence."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self._events: list[dict[str, Any]] = []
        if self.path and self.path.exists():
            self._load()

    def _load(self) -> None:
        assert self.path is not None
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            self._events.append(json.loads(line))

    def _persist(self, ev: dict[str, Any]) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    @property
    def length(self) -> int:
        return len(self._events)

    def last_hash(self) -> str:
        if not self._events:
            return GENESIS_PREV
        return self._events[-1]["event_hash"]

    def append(
        self,
        kind: str,
        lock_id: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if kind not in ALLOWED_KINDS:
            raise ValueError(f"invalid kind={kind}")
        seq = len(self._events) + 1
        ev: dict[str, Any] = {
            "schema_version": "1.0",
            "event_id": f"be_{uuid.uuid4().hex[:12]}",
            "seq": seq,
            "ts": _now(),
            "kind": kind,
            "lock_id": lock_id or "",
            "payload": dict(payload or {}),
            "prev_hash": self.last_hash(),
        }
        ev["event_hash"] = _hash(_event_body_for_hash(ev))
        self._events.append(ev)
        self._persist(ev)
        return ev

    def list_events(
        self,
        *,
        lock_id: str | None = None,
        kind: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        out = self._events
        if lock_id is not None:
            out = [e for e in out if e.get("lock_id") == lock_id]
        if kind is not None:
            out = [e for e in out if e.get("kind") == kind]
        if limit is not None:
            out = out[-limit:]
        return list(out)

    def verify_chain(self) -> dict[str, Any]:
        prev = GENESIS_PREV
        for i, ev in enumerate(self._events):
            if ev.get("prev_hash") != prev:
                return {
                    "ok": False,
                    "reason": "PREV_HASH_BREAK",
                    "seq": ev.get("seq"),
                    "index": i,
                }
            expected = _hash(_event_body_for_hash(ev))
            if ev.get("event_hash") != expected:
                return {
                    "ok": False,
                    "reason": "EVENT_HASH_MISMATCH",
                    "seq": ev.get("seq"),
                    "index": i,
                }
            prev = ev["event_hash"]
        return {"ok": True, "reason": "CHAIN_OK", "length": len(self._events)}

    def rewrite_forbidden(self, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError("bitacora is append-only; rewrite forbidden")
