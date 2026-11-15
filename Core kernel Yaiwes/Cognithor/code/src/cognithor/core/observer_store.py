"""SQLite persistence for Observer audit records.

Plain sqlite3 (not SQLCipher) — audit data is telemetry, not sensitive.
Responses and user messages are sha256-hashed before storage so the DB
does not contain verbatim content.
"""

from __future__ import annotations

import gc
import hashlib
import json
import sqlite3
import time
from dataclasses import asdict
from typing import TYPE_CHECKING

from cognithor.utils.logging import get_logger

if TYPE_CHECKING:
    from pathlib import Path

    from cognithor.core.observer import AuditResult

log = get_logger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audits (
    audit_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id        TEXT NOT NULL,
    timestamp         INTEGER NOT NULL,
    user_message_hash TEXT NOT NULL,
    response_hash     TEXT NOT NULL,
    model             TEXT NOT NULL,
    dimensions_json   TEXT NOT NULL,
    overall_passed    INTEGER NOT NULL,
    retry_count       INTEGER NOT NULL,
    final_action      TEXT NOT NULL,
    retry_strategy    TEXT,
    duration_ms       INTEGER NOT NULL,
    degraded_mode     INTEGER NOT NULL,
    error_type        TEXT
);
CREATE INDEX IF NOT EXISTS idx_session   ON audits(session_id);
CREATE INDEX IF NOT EXISTS idx_timestamp ON audits(timestamp);
CREATE INDEX IF NOT EXISTS idx_passed    ON audits(overall_passed);
"""


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


class AuditStore:
    """Append-only SQLite store for Observer audit records."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._initialized = False

    def _ensure_ready(self) -> None:
        if self._initialized:
            return
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        # Use explicit open/close so the file handle is released before any
        # rename attempt in _recover_from_corrupt() (critical on Windows).
        conn = sqlite3.connect(self._db_path)
        try:
            # Validate by running a simple PRAGMA before the schema creation.
            conn.execute("PRAGMA quick_check").fetchone()
            conn.executescript(_SCHEMA)
            conn.commit()
        finally:
            conn.close()
            del conn
            gc.collect()
        self._initialized = True

    def _recover_from_corrupt(self) -> None:
        """Move corrupted DB aside so a fresh one can be created."""
        if not self._db_path.exists():
            return
        broken = self._db_path.with_suffix(".broken.db")
        try:
            self._db_path.rename(broken)
            log.warning("observer_store_moved_corrupt_aside", broken_path=str(broken))
        except OSError as rename_err:
            log.warning(
                "observer_store_rename_failed",
                path=str(self._db_path),
                error=str(rename_err),
            )
        self._initialized = False

    def record(
        self,
        *,
        session_id: str,
        user_message: str,
        response: str,
        result: AuditResult,
    ) -> None:
        """Write one audit record. Fail-open on any I/O error."""
        try:
            self._ensure_ready()
        except sqlite3.DatabaseError as exc:
            log.warning("observer_store_corrupt_on_init", path=str(self._db_path), error=str(exc))
            self._recover_from_corrupt()
            try:
                self._ensure_ready()
            except Exception:
                log.warning("observer_store_unrecoverable", path=str(self._db_path))
                return

        log.debug(
            "observer.audit session=%s model=%s passed=%s",
            session_id,
            result.model,
            result.overall_passed,
        )
        dims_serialized = json.dumps(
            {name: asdict(dim) for name, dim in result.dimensions.items()},
            ensure_ascii=False,
        )

        backoffs = (0.05, 0.2, 0.5)  # 3 retries total
        for attempt, delay in enumerate((0.0, *backoffs)):
            if delay > 0:
                time.sleep(delay)
            try:
                with sqlite3.connect(self._db_path) as conn:
                    conn.execute(
                        "INSERT INTO audits (session_id, timestamp, user_message_hash, "
                        "response_hash, model, dimensions_json, overall_passed, retry_count, "
                        "final_action, retry_strategy, duration_ms, degraded_mode, error_type) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            session_id,
                            int(time.time() * 1000),
                            _sha256(user_message),
                            _sha256(response),
                            result.model,
                            dims_serialized,
                            int(result.overall_passed),
                            result.retry_count,
                            result.final_action,
                            result.retry_strategy,
                            result.duration_ms,
                            int(result.degraded_mode),
                            result.error_type,
                        ),
                    )
                return
            except sqlite3.DatabaseError as exc:
                if attempt == len(backoffs):
                    log.warning(
                        "observer_store_write_failed",
                        session_id=session_id,
                        error=str(exc),
                        attempts=attempt + 1,
                    )
                    return
                # else: retry after backoff
                continue
