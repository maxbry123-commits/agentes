"""Tests for incognito mode."""

from __future__ import annotations

from cognithor.gateway.session_store import SessionStore
from cognithor.models import SessionContext


def test_create_incognito_session(tmp_path):
    """Incognito session is persisted with flag."""
    store = SessionStore(tmp_path / "sessions.db")
    s = SessionContext(
        session_id="incog00000000001",
        user_id="web_user",
        channel="webui",
        agent_name="jarvis",
        incognito=True,
    )
    store.save_session(s)

    loaded = store.load_session("webui", "web_user")
    assert loaded is not None
    assert loaded.incognito is True


def test_incognito_listed_with_flag(tmp_path):
    """Session list includes incognito flag."""
    store = SessionStore(tmp_path / "sessions.db")
    s = SessionContext(
        session_id="incog00000000002",
        user_id="web_user",
        channel="webui",
        agent_name="jarvis",
        incognito=True,
    )
    store.save_session(s)

    sessions = store.list_sessions_for_channel("webui", "web_user")
    assert len(sessions) == 1
    assert sessions[0]["incognito"] is True


def test_non_incognito_default(tmp_path):
    """Regular sessions have incognito=False."""
    store = SessionStore(tmp_path / "sessions.db")
    s = SessionContext(
        session_id="regular000000001",
        user_id="web_user",
        channel="webui",
        agent_name="jarvis",
    )
    store.save_session(s)

    loaded = store.load_session("webui", "web_user")
    assert loaded is not None
    assert loaded.incognito is False


def test_incognito_survives_update(tmp_path):
    """Incognito flag is preserved when session is updated (ON CONFLICT)."""
    store = SessionStore(tmp_path / "sessions.db")
    s = SessionContext(
        session_id="incog00000000003",
        user_id="web_user",
        channel="webui",
        agent_name="jarvis",
        incognito=True,
    )
    store.save_session(s)

    # Simulate an update (same session_id, new message count)
    s.message_count = 5
    store.save_session(s)

    loaded = store.load_session("webui", "web_user")
    assert loaded is not None
    assert loaded.incognito is True
    assert loaded.message_count == 5


def test_incognito_field_in_model():
    """SessionContext has incognito field with default False."""
    s = SessionContext(session_id="test0000000000001")
    assert s.incognito is False

    s2 = SessionContext(session_id="test0000000000002", incognito=True)
    assert s2.incognito is True
