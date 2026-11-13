"""A message typed while a turn is live must never vanish. send_message used to
early-return when the session's task was still running, dropping the prompt with
no bubble and no trace. It now queues the full send, and the turn task's done
callback replays it the moment the agent is free.

Run with:  backend/.venv/bin/python -m pytest backend/tests/test_mid_turn_message_queue.py
"""
import asyncio

import pytest

from backend.apps.agents import agent_manager as am
from backend.apps.agents.core.models import AgentSession
import backend.apps.agents.core.ws_manager as ws_mod


@pytest.fixture(autouse=True)
def p_quiet_ws(monkeypatch):
    async def fake_send(session_id, event, data):
        return None
    monkeypatch.setattr(ws_mod.ws_manager, "send_to_session", fake_send, raising=True)


def p_manager(monkeypatch, ran, gate):
    mgr = am.AgentManager()
    session = AgentSession(name="t", model="sonnet")
    mgr.sessions[session.id] = session

    async def fake_loop(session_id, prompt, **kwargs):
        ran.append(prompt)
        await gate.wait()

    async def fake_label(*a, **k):
        return None

    monkeypatch.setattr(mgr, "run_agent_loop", fake_loop)
    monkeypatch.setattr(mgr, "generate_turn_label", fake_label)
    from backend.apps.agents.browser import browser_fast_path
    monkeypatch.setattr(browser_fast_path, "fast_path_eligible", lambda *a, **k: False)
    return mgr, session


@pytest.mark.asyncio
async def test_mid_turn_message_is_queued_then_replayed(monkeypatch):
    ran = []
    gate = asyncio.Event()
    mgr, session = p_manager(monkeypatch, ran, gate)

    await mgr.send_message(session.id, "first", client_message_id="c1")
    await asyncio.sleep(0)  # let the created turn task actually start
    assert ran == ["first"]

    await mgr.send_message(session.id, "second", client_message_id="c2")
    # Queued, not dropped; not yet appended either (the running CLI turn can't see it anyway).
    assert [q.prompt for q in mgr.pending_messages[session.id]] == ["second"]
    assert [m.content for m in session.messages if m.role == "user"] == ["first"]

    gate.set()
    await mgr.tasks[session.id]
    for _ in range(50):
        if len(ran) == 2:
            break
        await asyncio.sleep(0.01)

    assert ran == ["first", "second"]
    user_msgs = [m for m in session.messages if m.role == "user"]
    assert [m.content for m in user_msgs] == ["first", "second"]
    # The original client id round-trips, so the UI's pending optimistic bubble reconciles.
    assert user_msgs[1].client_message_id == "c2"
    assert session.id not in mgr.pending_messages


@pytest.mark.asyncio
async def test_multiple_queued_messages_replay_in_order(monkeypatch):
    ran = []
    p_first_gate = asyncio.Event()
    mgr, session = p_manager(monkeypatch, ran, p_first_gate)

    async def p_fast_loop(session_id, prompt, **kwargs):
        ran.append(prompt)

    await mgr.send_message(session.id, "one")  # blocks on p_first_gate
    await asyncio.sleep(0)
    monkeypatch.setattr(mgr, "run_agent_loop", p_fast_loop)
    await mgr.send_message(session.id, "two")
    await mgr.send_message(session.id, "three")
    assert [q.prompt for q in mgr.pending_messages[session.id]] == ["two", "three"]

    p_first_gate.set()
    await mgr.tasks[session.id]
    for _ in range(50):
        if len(ran) == 3:
            break
        await asyncio.sleep(0.01)

    assert ran == ["one", "two", "three"]
    assert session.id not in mgr.pending_messages
