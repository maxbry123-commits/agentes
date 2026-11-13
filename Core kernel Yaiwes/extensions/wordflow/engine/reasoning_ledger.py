# -*- coding: utf-8 -*-
"""Reasoning Ledger / Decision Memory — T0l. Append-only frames. 0% LLM."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .goal_lock import verify_lock_integrity

GENESIS_PREV = "0" * 64


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hash(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _frame_body_for_hash(frame: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": frame["schema_version"],
        "frame_id": frame["frame_id"],
        "seq": frame["seq"],
        "lock_id": frame["lock_id"],
        "ts": frame["ts"],
        "goal": frame["goal"],
        "evidence": list(frame.get("evidence") or []),
        "decision": frame["decision"],
        "alternatives": list(frame.get("alternatives") or []),
        "refutations": list(frame.get("refutations") or []),
        "tools": list(frame.get("tools") or []),
        "artifacts": list(frame.get("artifacts") or []),
        "confidence": frame.get("confidence"),
        "checkpoint_id": frame.get("checkpoint_id"),
        "prev_hash": frame["prev_hash"],
    }


class ReasoningLedger:
    """Append-only decision memory. Optional JSONL path."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self._frames: list[dict[str, Any]] = []
        if self.path and self.path.exists():
            self._load()

    def _load(self) -> None:
        assert self.path is not None
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                self._frames.append(json.loads(line))

    def _persist(self, frame: dict[str, Any]) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(frame, ensure_ascii=False) + "\n")

    @property
    def length(self) -> int:
        return len(self._frames)

    def last_hash(self) -> str:
        if not self._frames:
            return GENESIS_PREV
        return self._frames[-1]["frame_hash"]

    def append_frame(
        self,
        lock: dict[str, Any],
        *,
        decision: str,
        evidence: list[str] | None = None,
        alternatives: list[str] | None = None,
        refutations: list[str] | None = None,
        tools: list[str] | None = None,
        artifacts: list[str] | None = None,
        confidence: float | None = None,
        checkpoint_id: str | None = None,
        require_lock_intact: bool = True,
    ) -> dict[str, Any]:
        if require_lock_intact:
            integ = verify_lock_integrity(lock)
            if not integ["ok"]:
                raise ValueError(f"lock not intact: {integ.get('reason')}")

        if not (decision or "").strip():
            raise ValueError("decision required")
        if confidence is not None and (confidence < 0 or confidence > 1):
            raise ValueError("confidence must be 0..1")

        goal = lock.get("objective") or ""
        frame: dict[str, Any] = {
            "schema_version": "1.0",
            "frame_id": f"rl_{uuid.uuid4().hex[:12]}",
            "seq": len(self._frames) + 1,
            "lock_id": lock.get("lock_id") or "",
            "ts": _now(),
            "goal": goal,
            "evidence": [str(e) for e in (evidence or [])],
            "decision": decision.strip(),
            "alternatives": [str(a) for a in (alternatives or [])],
            "refutations": [str(r) for r in (refutations or [])],
            "tools": [str(t) for t in (tools or [])],
            "artifacts": [str(a) for a in (artifacts or [])],
            "confidence": confidence,
            "checkpoint_id": checkpoint_id,
            "prev_hash": self.last_hash(),
        }
        frame["frame_hash"] = _hash(_frame_body_for_hash(frame))
        self._frames.append(frame)
        self._persist(frame)
        return frame

    def list_frames(
        self,
        *,
        lock_id: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        out = self._frames
        if lock_id is not None:
            out = [f for f in out if f.get("lock_id") == lock_id]
        if limit is not None:
            out = out[-limit:]
        return list(out)

    def verify_chain(self) -> dict[str, Any]:
        prev = GENESIS_PREV
        for i, fr in enumerate(self._frames):
            if fr.get("prev_hash") != prev:
                return {"ok": False, "reason": "PREV_HASH_BREAK", "seq": fr.get("seq"), "index": i}
            expected = _hash(_frame_body_for_hash(fr))
            if fr.get("frame_hash") != expected:
                return {
                    "ok": False,
                    "reason": "FRAME_HASH_MISMATCH",
                    "seq": fr.get("seq"),
                    "index": i,
                }
            prev = fr["frame_hash"]
        return {"ok": True, "reason": "CHAIN_OK", "length": len(self._frames)}

    def rewrite_forbidden(self) -> None:
        raise RuntimeError("reasoning ledger is append-only; rewrite forbidden")
