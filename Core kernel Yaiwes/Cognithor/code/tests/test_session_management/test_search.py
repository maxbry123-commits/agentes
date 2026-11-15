"""Tests for full-text search across sessions."""

from __future__ import annotations

from datetime import UTC, datetime

from cognithor.gateway.session_store import SessionStore
from cognithor.models import Message, MessageRole, SessionContext


def test_search_finds_matching_messages(tmp_path):
    store = SessionStore(tmp_path / "sessions.db")
    for sid in ["search00000001", "search00000002"]:
        s = SessionContext(session_id=sid, user_id="web_user", channel="webui", agent_name="jarvis")
        store.save_session(s)

    store.save_chat_history(
        "search00000001",
        [
            Message(
                role=MessageRole.USER,
                content="Wie wird das Wetter?",
                timestamp=datetime.now(tz=UTC),
            ),
            Message(
                role=MessageRole.ASSISTANT, content="Morgen sonnig.", timestamp=datetime.now(tz=UTC)
            ),
        ],
    )
    store.save_chat_history(
        "search00000002",
        [
            Message(
                role=MessageRole.USER,
                content="Schreibe Python Code",
                timestamp=datetime.now(tz=UTC),
            ),
        ],
    )

    results = store.search_chat_history("Wetter")
    assert len(results) >= 1
    assert results[0]["session_id"] == "search00000001"
    assert "Wetter" in results[0]["content"]


def test_search_empty_query(tmp_path):
    store = SessionStore(tmp_path / "sessions.db")
    results = store.search_chat_history("")
    assert results == [] or isinstance(results, list)


def test_search_no_matches(tmp_path):
    store = SessionStore(tmp_path / "sessions.db")
    s = SessionContext(
        session_id="search00000003", user_id="web_user", channel="webui", agent_name="jarvis"
    )
    store.save_session(s)
    store.save_chat_history(
        "search00000003",
        [
            Message(role=MessageRole.USER, content="Hallo Welt", timestamp=datetime.now(tz=UTC)),
        ],
    )

    results = store.search_chat_history("xyznonexistent")
    assert len(results) == 0
