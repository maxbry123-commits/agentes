"""Tests for jarvis.core.config_versioning."""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING

import pytest

from cognithor.core.config_versioning import (
    _MAX_REVISIONS,
    _cleanup_old_revisions,
    list_revisions,
    rollback_to,
    save_config_revision,
    set_revisions_dir,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(autouse=True)
def _temp_revisions_dir(tmp_path: Path):
    """Use a temporary directory for revisions during tests."""
    revisions_dir = tmp_path / "config_revisions"
    revisions_dir.mkdir()
    set_revisions_dir(revisions_dir)
    yield revisions_dir
    set_revisions_dir(None)


SAMPLE_CONFIG = {
    "owner_name": "TestUser",
    "language": "en",
    "ollama": {"base_url": "http://localhost:11434"},
}


class TestSaveConfigRevision:
    def test_returns_revision_id(self):
        rev_id = save_config_revision(SAMPLE_CONFIG, reason="test save")
        assert rev_id.startswith("rev_")

    def test_creates_file(self, _temp_revisions_dir: Path):
        rev_id = save_config_revision(SAMPLE_CONFIG, reason="test file")
        filepath = _temp_revisions_dir / f"{rev_id}.json"
        assert filepath.exists()

    def test_file_contains_config(self, _temp_revisions_dir: Path):
        rev_id = save_config_revision(SAMPLE_CONFIG, reason="test content")
        filepath = _temp_revisions_dir / f"{rev_id}.json"
        data = json.loads(filepath.read_text(encoding="utf-8"))
        assert data["config"] == SAMPLE_CONFIG
        assert data["reason"] == "test content"
        assert data["revision_id"] == rev_id
        assert "timestamp" in data

    def test_empty_reason_default(self):
        rev_id = save_config_revision(SAMPLE_CONFIG)
        revisions = list_revisions()
        rev = next(r for r in revisions if r["revision_id"] == rev_id)
        assert rev["reason"] == ""


class TestListRevisions:
    def test_empty_initially(self):
        assert list_revisions() == []

    def test_returns_saved_revisions(self):
        save_config_revision(SAMPLE_CONFIG, reason="r1")
        time.sleep(0.01)  # ensure different timestamps
        save_config_revision(SAMPLE_CONFIG, reason="r2")
        revisions = list_revisions()
        assert len(revisions) == 2
        # Newest first
        assert revisions[0]["reason"] == "r2"
        assert revisions[1]["reason"] == "r1"

    def test_revision_fields(self):
        save_config_revision(SAMPLE_CONFIG, reason="field check")
        revisions = list_revisions()
        rev = revisions[0]
        assert "revision_id" in rev
        assert "timestamp" in rev
        assert "reason" in rev
        # Config should NOT be in the listing (too large)
        assert "config" not in rev


class TestRollbackTo:
    def test_rollback_returns_config(self):
        rev_id = save_config_revision(SAMPLE_CONFIG, reason="rollback test")
        config = rollback_to(rev_id)
        assert config == SAMPLE_CONFIG

    def test_rollback_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError, match="not found"):
            rollback_to("rev_0000000000000")

    def test_rollback_corrupt_file(self, _temp_revisions_dir: Path):
        filepath = _temp_revisions_dir / "rev_9999999999999.json"
        filepath.write_text("not json", encoding="utf-8")
        with pytest.raises(ValueError, match="corrupt"):
            rollback_to("rev_9999999999999")

    def test_rollback_missing_config_key(self, _temp_revisions_dir: Path):
        filepath = _temp_revisions_dir / "rev_8888888888888.json"
        filepath.write_text(json.dumps({"revision_id": "x", "timestamp": 0}), encoding="utf-8")
        with pytest.raises(ValueError, match="no valid config"):
            rollback_to("rev_8888888888888")


class TestCleanupOldRevisions:
    def test_keeps_max_revisions(self, _temp_revisions_dir: Path):
        # Create MAX + 10 revisions
        for i in range(_MAX_REVISIONS + 10):
            ts = 1000000000000 + i
            filepath = _temp_revisions_dir / f"rev_{ts}.json"
            payload = {
                "revision_id": f"rev_{ts}",
                "timestamp": ts / 1000.0,
                "reason": f"bulk {i}",
                "config": SAMPLE_CONFIG,
            }
            filepath.write_text(json.dumps(payload), encoding="utf-8")

        _cleanup_old_revisions()

        remaining = list(_temp_revisions_dir.glob("rev_*.json"))
        assert len(remaining) == _MAX_REVISIONS

    def test_removes_oldest(self, _temp_revisions_dir: Path):
        # Create MAX + 5 revisions
        for i in range(_MAX_REVISIONS + 5):
            ts = 2000000000000 + i
            filepath = _temp_revisions_dir / f"rev_{ts}.json"
            payload = {
                "revision_id": f"rev_{ts}",
                "timestamp": ts / 1000.0,
                "reason": f"bulk {i}",
                "config": SAMPLE_CONFIG,
            }
            filepath.write_text(json.dumps(payload), encoding="utf-8")

        _cleanup_old_revisions()

        remaining_names = sorted(f.stem for f in _temp_revisions_dir.glob("rev_*.json"))
        # The oldest 5 should be gone
        for i in range(5):
            ts = 2000000000000 + i
            assert f"rev_{ts}" not in remaining_names

    def test_no_cleanup_under_max(self, _temp_revisions_dir: Path):
        for i in range(3):
            save_config_revision(SAMPLE_CONFIG, reason=f"small {i}")
            time.sleep(0.002)

        _cleanup_old_revisions()

        remaining = list(_temp_revisions_dir.glob("rev_*.json"))
        assert len(remaining) == 3
