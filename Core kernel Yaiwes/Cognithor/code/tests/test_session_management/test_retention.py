"""Tests for GDPR retention enforcement."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from cognithor.gateway.session_store import SessionStore
from cognithor.models import SessionContext


def test_cleanup_old_sessions(tmp_path):
    """Sessions older than max_age_days are deactivated."""
    store = SessionStore(tmp_path / "sessions.db")

    old = SessionContext(
        session_id="old0000000000001",
        user_id="web_user",
        channel="webui",
        agent_name="jarvis",
    )
    old.last_activity = datetime.now(tz=UTC) - timedelta(days=60)
    store.save_session(old)

    recent = SessionContext(
        session_id="new0000000000001",
        user_id="web_user",
        channel="webui",
        agent_name="jarvis",
    )
    store.save_session(recent)

    cleaned = store.cleanup_old_sessions(max_age_days=30)
    assert cleaned == 1

    sessions = store.list_sessions_for_channel("webui", "web_user")
    assert len(sessions) == 1
    assert sessions[0]["id"] == "new0000000000001"


def test_cleanup_keeps_recent(tmp_path):
    """Recent sessions are not affected by cleanup."""
    store = SessionStore(tmp_path / "sessions.db")
    s = SessionContext(
        session_id="keep000000000001",
        user_id="web_user",
        channel="webui",
        agent_name="jarvis",
    )
    store.save_session(s)

    cleaned = store.cleanup_old_sessions(max_age_days=30)
    assert cleaned == 0
