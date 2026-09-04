"""Durable append-only audit history with hash-chain verification.

The store is deliberately local and deterministic: no AI provider, router, or
external service is required. Each event records the previous event hash and
its own canonical SHA-256 hash. Verification detects truncation, reordering,
mutation, and duplicate sequence numbers.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


class AuditHistory:
    """Append-only JSONL event log with a cryptographic hash chain."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError("AUDIT_EVENT_NOT_OBJECT")
            rows.append(row)
        return rows

    def append(self, *, event: str, task_id: str, status: str, evidence: dict[str, Any] | None = None,
               revision: str = "", metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        if not event or not task_id or not status:
            raise ValueError("AUDIT_EVENT_FIELDS_REQUIRED")
        rows = self._read()
        previous = rows[-1]["event_hash"] if rows else None
        sequence = len(rows) + 1
        body = {
            "schema_version": "1.0",
            "sequence": sequence,
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "task_id": task_id,
            "status": status,
            "revision": revision,
            "previous_hash": previous,
            "evidence": dict(evidence or {}),
            "metadata": dict(metadata or {}),
            "llm_control": "DENY",
        }
        body["event_hash"] = _hash({k: v for k, v in body.items() if k != "event_hash"})
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(_canonical(body) + "\n")
        return body

    def verify(self) -> dict[str, Any]:
        rows = self._read()
        previous = None
        for expected_sequence, row in enumerate(rows, start=1):
            if row.get("sequence") != expected_sequence:
                return {"ok": False, "reason": "SEQUENCE_MISMATCH", "sequence": expected_sequence}
            if row.get("previous_hash") != previous:
                return {"ok": False, "reason": "PARENT_HASH_MISMATCH", "sequence": expected_sequence}
            expected_hash = _hash({k: v for k, v in row.items() if k != "event_hash"})
            if row.get("event_hash") != expected_hash:
                return {"ok": False, "reason": "HASH_MISMATCH", "sequence": expected_sequence}
            previous = row["event_hash"]
        return {"ok": True, "count": len(rows), "tip_hash": previous}

    def replay(self) -> list[dict[str, Any]]:
        result = self.verify()
        if not result["ok"]:
            raise ValueError(f"AUDIT_HISTORY_INVALID:{result['reason']}")
        return self._read()

    def replace_for_test(self, rows: list[dict[str, Any]]) -> None:
        """Test-only helper: atomically replace the log to exercise detection."""
        fd, tmp_name = tempfile.mkstemp(prefix="audit-history-", suffix=".jsonl", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                for row in rows:
                    handle.write(_canonical(row) + "\n")
            os.replace(tmp_name, self.path)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
