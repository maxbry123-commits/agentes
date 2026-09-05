# -*- coding: utf-8 -*-
"""CheckpointStore — T18. Save/restore execution state. 0% LLM."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hash(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _body(cp: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": cp["schema_version"],
        "checkpoint_id": cp["checkpoint_id"],
        "lock_id": cp["lock_id"],
        "task_id": cp.get("task_id"),
        "created_at": cp["created_at"],
        "label": cp.get("label"),
        "state": cp.get("state") or {},
    }


class CheckpointStore:
    """In-memory + optional JSONL directory of checkpoints."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self._by_id: dict[str, dict[str, Any]] = {}
        if self.path and self.path.exists():
            self._load()

    def _load(self) -> None:
        assert self.path is not None
        if self.path.is_file():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    cp = json.loads(line)
                    self._by_id[cp["checkpoint_id"]] = cp

    def _persist(self, cp: dict[str, Any]) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(cp, ensure_ascii=False) + "\n")

    def save(
        self,
        *,
        lock_id: str,
        state: dict[str, Any],
        task_id: str | None = None,
        label: str | None = None,
        checkpoint_id: str | None = None,
    ) -> dict[str, Any]:
        if not lock_id:
            raise ValueError("lock_id required")
        if not isinstance(state, dict):
            raise ValueError("state must be dict")
        cp: dict[str, Any] = {
            "schema_version": "1.0",
            "checkpoint_id": checkpoint_id or f"cp_{uuid.uuid4().hex[:12]}",
            "lock_id": lock_id,
            "task_id": task_id,
            "created_at": _now(),
            "label": label,
            "state": dict(state),
        }
        cp["checkpoint_hash"] = _hash(_body(cp))
        self._by_id[cp["checkpoint_id"]] = cp
        self._persist(cp)
        return dict(cp)

    def get(self, checkpoint_id: str) -> dict[str, Any] | None:
        cp = self._by_id.get(checkpoint_id)
        return dict(cp) if cp else None

    def verify(self, cp: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(cp, dict):
            return {"ok": False, "reason": "INVALID"}
        expected = _hash(_body(cp))
        if cp.get("checkpoint_hash") != expected:
            return {"ok": False, "reason": "HASH_MISMATCH"}
        return {"ok": True, "reason": "CHECKPOINT_OK", "checkpoint_id": cp.get("checkpoint_id")}

    def restore(self, checkpoint_id: str) -> dict[str, Any]:
        """Return verified state payload."""
        cp = self._by_id.get(checkpoint_id)
        if cp is None:
            return {"ok": False, "reason": "NOT_FOUND"}
        v = self.verify(cp)
        if not v["ok"]:
            return v
        return {
            "ok": True,
            "reason": "RESTORED",
            "checkpoint_id": checkpoint_id,
            "lock_id": cp["lock_id"],
            "task_id": cp.get("task_id"),
            "state": dict(cp.get("state") or {}),
        }

    def list_for_lock(self, lock_id: str) -> list[dict[str, Any]]:
        return [dict(cp) for cp in self._by_id.values() if cp.get("lock_id") == lock_id]
