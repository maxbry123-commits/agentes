"""Pins generate_title (lifted into manager/metadata.py): the no-session guard and
the fallback-to-truncated-prompt path when the aux LLM is unavailable."""

import asyncio

import backend.apps.agents.manager.metadata as md
import backend.apps.agents.providers.registry as registry
from backend.apps.agents.core.models import AgentSession


def test_generate_title_raises_without_session():
    try:
        asyncio.run(md.generate_title(None, "sid", "hello"))
        assert False, "expected ValueError when the session is missing"
    except ValueError:
        pass


def test_generate_title_falls_back_to_truncated_prompt_when_aux_unavailable(monkeypatch):
    sent = []

    async def fake_send(session_id, event, data):
        sent.append((event, data))

    async def boom(*a, **k):
        raise RuntimeError("aux model unavailable")

    monkeypatch.setattr(md.ws_manager, "send_to_session", fake_send, raising=True)
    monkeypatch.setattr(registry, "resolve_aux_model", boom, raising=True)

    session = AgentSession(name="x", model="sonnet")
    prompt = "Plan me a really long trip to Tokyo with many stops and details everywhere"
    title = asyncio.run(md.generate_title(session, "sid", prompt))

    assert title == prompt[:40].strip()      # fell back to the truncated prompt
    assert session.name == title             # still labels the session
    assert any(e == "agent:name_updated" for e, _ in sent)  # and notifies the UI


def test_generate_turn_label_is_silent_on_aux_failure(monkeypatch):
    sent = []

    async def fake_send(session_id, event, data):
        sent.append((event, data))

    async def boom(*a, **k):
        raise RuntimeError("aux model unavailable")

    monkeypatch.setattr(md.ws_manager, "send_to_session", fake_send, raising=True)
    monkeypatch.setattr(registry, "resolve_aux_model", boom, raising=True)

    session = AgentSession(name="x", model="sonnet")
    # best-effort: must NOT raise, and emits no label (the heuristic narrator stands in)
    asyncio.run(md.generate_turn_label(session, "sid", "turn-1", "do a thing"))
    assert not any(e == "agent:turn_label" for e, _ in sent)


def test_generate_group_meta_raises_without_session():
    try:
        asyncio.run(md.generate_group_meta(None, "sid", "g1", [{"tool": "Gmail"}]))
        assert False, "expected ValueError when the session is missing"
    except ValueError:
        pass


def test_generate_group_meta_falls_back_to_tool_name_when_aux_unavailable(monkeypatch):
    sent = []

    async def fake_send(session_id, event, data):
        sent.append((event, data))

    async def boom(*a, **k):
        raise RuntimeError("aux model unavailable")

    monkeypatch.setattr(md.ws_manager, "send_to_session", fake_send, raising=True)
    monkeypatch.setattr(registry, "resolve_aux_model", boom, raising=True)

    session = AgentSession(name="x", model="sonnet")
    result = asyncio.run(md.generate_group_meta(session, "sid", "g1", [{"tool": "mcp__gmail__send_email"}]))

    assert result["name"] == "Send Email"    # fallback: last __ segment, humanized
    assert result["svg"] == ""
    assert "g1" in session.tool_group_meta    # still records the group
    assert any(e == "agent:group_meta_updated" for e, _ in sent)
