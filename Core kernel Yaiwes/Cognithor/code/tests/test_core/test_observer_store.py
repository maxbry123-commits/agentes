"""Tests for AuditStore SQLite persistence."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from cognithor.core.observer import AuditResult, DimensionResult
from cognithor.core.observer_store import AuditStore

if TYPE_CHECKING:
    from pathlib import Path


def _make_result(**kwargs: object) -> AuditResult:
    defaults: dict[str, object] = {
        "overall_passed": True,
        "dimensions": {
            "hallucination": DimensionResult(
                name="hallucination", passed=True, reason="", evidence="", fix_suggestion=""
            ),
        },
        "retry_count": 0,
        "final_action": "pass",
        "retry_strategy": "deliver",
        "model": "qwen3:32b",
        "duration_ms": 3200,
        "degraded_mode": False,
        "error_type": None,
    }
    defaults.update(kwargs)
    return AuditResult(**defaults)  # type: ignore[arg-type]


class TestAuditStoreSchema:
    def test_creates_db_lazily(self, tmp_path: Path):
        db_path = tmp_path / "audits.db"
        assert not db_path.exists()
        store = AuditStore(db_path=db_path)
        # Just constructing should NOT create the DB.
        assert not db_path.exists()
        # First record triggers creation.
        store.record(session_id="s1", user_message="Q", response="A", result=_make_result())
        assert db_path.exists()

    def test_schema_has_expected_columns(self, tmp_path: Path):
        db_path = tmp_path / "audits.db"
        store = AuditStore(db_path=db_path)
        store.record(session_id="s1", user_message="Q", response="A", result=_make_result())
        with sqlite3.connect(db_path) as conn:
            cols = {row[1] for row in conn.execute("PRAGMA table_info(audits)").fetchall()}
        assert cols == {
            "audit_id",
            "session_id",
            "timestamp",
            "user_message_hash",
            "response_hash",
            "model",
            "dimensions_json",
            "overall_passed",
            "retry_count",
            "final_action",
            "retry_strategy",
            "duration_ms",
            "degraded_mode",
            "error_type",
        }


class TestAuditStoreRecord:
    def test_writes_one_row(self, tmp_path: Path):
        store = AuditStore(db_path=tmp_path / "a.db")
        store.record(session_id="s1", user_message="Q", response="A", result=_make_result())
        with sqlite3.connect(tmp_path / "a.db") as conn:
            rows = conn.execute("SELECT COUNT(*) FROM audits").fetchone()
        assert rows[0] == 1

    def test_user_and_response_hashed(self, tmp_path: Path):
        store = AuditStore(db_path=tmp_path / "a.db")
        store.record(
            session_id="s1",
            user_message="sensitive user question",
            response="sensitive answer",
            result=_make_result(),
        )
        with sqlite3.connect(tmp_path / "a.db") as conn:
            umh, rh = conn.execute("SELECT user_message_hash, response_hash FROM audits").fetchone()
        # 64-char sha256 hex, NOT the raw message.
        assert len(umh) == 64 and "sensitive" not in umh
        assert len(rh) == 64 and "sensitive" not in rh


class TestAuditStoreErrorHandling:
    def test_locked_db_retries_then_gives_up(self, tmp_path: Path, monkeypatch):
        store = AuditStore(db_path=tmp_path / "a.db")
        store._ensure_ready()  # create the DB once

        # Patch sqlite3.connect to always raise OperationalError("database is locked")
        call_count = {"n": 0}

        class _LockedConn:
            def __enter__(self):
                raise sqlite3.OperationalError("database is locked")

            def __exit__(self, *a):
                return False

        def _fake_connect(*args, **kwargs):
            call_count["n"] += 1
            return _LockedConn()

        monkeypatch.setattr("sqlite3.connect", _fake_connect)

        # Must NOT raise — fail-open contract.
        store.record(
            session_id="s1",
            user_message="Q",
            response="A",
            result=_make_result(),
        )
        # 3 retries after initial attempt = 4 total connect calls, with backoff.
        assert call_count["n"] == 4

    def test_corrupt_db_moved_aside_on_init(self, tmp_path: Path):
        db = tmp_path / "a.db"
        # Create a corrupt file (non-sqlite bytes)
        db.write_bytes(b"this is not a valid sqlite file")
        store = AuditStore(db_path=db)
        # record() should detect + recover
        store.record(session_id="s1", user_message="Q", response="A", result=_make_result())
        # Original corrupt file should be moved aside
        assert (tmp_path / "a.broken.db").exists()
        # Fresh DB should work
        with sqlite3.connect(db) as conn:
            rows = conn.execute("SELECT COUNT(*) FROM audits").fetchone()
        assert rows[0] == 1

    def test_disk_full_logged_not_raised(self, tmp_path: Path, monkeypatch):
        store = AuditStore(db_path=tmp_path / "a.db")
        store._ensure_ready()

        def _disk_full(*args, **kwargs):
            raise sqlite3.OperationalError("disk I/O error")

        monkeypatch.setattr("sqlite3.connect", _disk_full)
        # Must NOT raise
        store.record(session_id="s1", user_message="Q", response="A", result=_make_result())
