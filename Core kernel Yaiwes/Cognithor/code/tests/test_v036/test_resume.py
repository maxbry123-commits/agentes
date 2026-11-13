"""Tests for Feature 3: Resume-as-Tool-Call."""

from __future__ import annotations

import sys

from cognithor.core.checkpointing import (
    CheckpointStore,
    PersistentCheckpoint,
)


class TestPersistentCheckpoint:
    def test_json_roundtrip(self):
        cp = PersistentCheckpoint(
            session_id="sess-123",
            agent_id="agent-1",
            state={"messages": ["hello"], "last_successful_tool": "web_search"},
        )
        json_str = cp.to_json()
        cp2 = PersistentCheckpoint.from_json(json_str)
        assert cp2.session_id == "sess-123"
        assert cp2.agent_id == "agent-1"
        assert cp2.state["last_successful_tool"] == "web_search"
        assert cp2.platform == sys.platform

    def test_checkpoint_has_timestamp(self):
        cp = PersistentCheckpoint(session_id="s1")
        assert cp.timestamp_utc  # Not empty

    def test_checkpoint_has_id(self):
        cp = PersistentCheckpoint(session_id="s1")
        assert len(cp.checkpoint_id) == 16


class TestCheckpointStore:
    def test_save_and_load(self, tmp_path):
        store = CheckpointStore(tmp_path / "checkpoints")
        cp = PersistentCheckpoint(
            session_id="session-abc",
            state={"tool_call_stack": ["read_file", "web_search"]},
        )
        store.save(cp)

        loaded = store.load("session-abc", cp.checkpoint_id)
        assert loaded is not None
        assert loaded.session_id == "session-abc"
        assert loaded.state["tool_call_stack"] == ["read_file", "web_search"]

    def test_load_nonexistent_returns_none(self, tmp_path):
        store = CheckpointStore(tmp_path / "checkpoints")
        assert store.load("nope", "nope") is None

    def test_get_latest(self, tmp_path):
        store = CheckpointStore(tmp_path / "checkpoints")

        cp1 = PersistentCheckpoint(
            session_id="s1", state={"step": 1}, timestamp_utc="2026-01-01T00:00:00"
        )
        store.save(cp1)

        cp2 = PersistentCheckpoint(
            session_id="s1", state={"step": 2}, timestamp_utc="2026-01-01T00:00:01"
        )
        store.save(cp2)

        latest = store.get_latest("s1")
        assert latest is not None
        assert latest.state["step"] == 2

    def test_resume_without_checkpoint_id_uses_latest(self, tmp_path):
        store = CheckpointStore(tmp_path / "checkpoints")
        cp = PersistentCheckpoint(session_id="s1", state={"resume_hint": "continue"})
        store.save(cp)

        latest = store.get_latest("s1")
        assert latest is not None
        assert latest.state["resume_hint"] == "continue"

    def test_list_checkpoints(self, tmp_path):
        store = CheckpointStore(tmp_path / "checkpoints")
        for i in range(3):
            store.save(PersistentCheckpoint(session_id="s1", state={"i": i}))

        ids = store.list_checkpoints("s1")
        assert len(ids) == 3

    def test_clear_session(self, tmp_path):
        store = CheckpointStore(tmp_path / "checkpoints")
        store.save(PersistentCheckpoint(session_id="s1", state={}))
        store.save(PersistentCheckpoint(session_id="s1", state={}))

        deleted = store.clear_session("s1")
        assert deleted == 2
        assert store.list_checkpoints("s1") == []

    def test_checkpoint_path_is_platform_correct(self, tmp_path):
        """Checkpoint directory uses pathlib — no hardcoded separators."""
        store = CheckpointStore(tmp_path / "checkpoints")
        cp = PersistentCheckpoint(session_id="test-sess")
        path = store.save(cp)
        assert path.exists()
        assert path.suffix == ".json"
        # Path should be relative to checkpoints dir
        assert "test-sess" in str(path)
