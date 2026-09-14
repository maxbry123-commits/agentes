"""Tests for project/folder grouping."""

from __future__ import annotations

from cognithor.gateway.session_store import SessionStore
from cognithor.models import SessionContext


def test_list_sessions_by_folder(tmp_path):
    """Filter sessions by folder returns only matching."""
    store = SessionStore(tmp_path / "sessions.db")
    for i, folder in enumerate(["work", "work", "personal"]):
        s = SessionContext(
            session_id=f"proj{i:013d}",
            user_id="web_user",
            channel="webui",
            agent_name="jarvis",
        )
        store.save_session(s)
        store.update_session_folder(f"proj{i:013d}", folder)

    work = store.list_sessions_by_folder("work")
    assert len(work) == 2
    assert all(s["folder"] == "work" for s in work)

    personal = store.list_sessions_by_folder("personal")
    assert len(personal) == 1
    assert personal[0]["folder"] == "personal"


def test_list_sessions_by_folder_empty(tmp_path):
    """Nonexistent folder returns empty list."""
    store = SessionStore(tmp_path / "sessions.db")
    result = store.list_sessions_by_folder("nonexistent")
    assert result == []


def test_list_folders_distinct(tmp_path):
    """list_folders returns distinct folder names."""
    store = SessionStore(tmp_path / "sessions.db")
    for i, folder in enumerate(["alpha", "beta", "alpha", "gamma"]):
        s = SessionContext(
            session_id=f"fold{i:013d}",
            user_id="web_user",
            channel="webui",
            agent_name="jarvis",
        )
        store.save_session(s)
        store.update_session_folder(f"fold{i:013d}", folder)

    folders = store.list_folders(channel="webui", user_id="web_user")
    assert sorted(folders) == ["alpha", "beta", "gamma"]
