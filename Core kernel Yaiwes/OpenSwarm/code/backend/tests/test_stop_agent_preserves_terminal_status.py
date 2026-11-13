"""Stopping is for LIVE turns. A settled chat must come back settled.

Found live: quit the app and relaunch, and every finished conversation came back labelled
"stopped" with a Resume button hanging off an answer that was already delivered. The chain is
short. `self.tasks[session_id]` is written when a turn starts and only removed by stop/close, so a
completed session leaves its done task in the registry forever; the agents sub-app's shutdown hook
loops over every task it finds and calls `stop_agent` on each; `stop_agent` then wrote
`status = "stopped"` unconditionally. One ordinary session was enough to reproduce it.

The guard belongs in `stop_agent`, not in the shutdown loop, so no future caller can express the
bad state either. `close_session` already had exactly this guard, which is what made the
inconsistency easy to miss.

Run:
    cd backend && .venv/bin/python -m pytest tests/test_stop_agent_preserves_terminal_status.py -v
"""

from __future__ import annotations

import pytest

from backend.apps.agents.agent_manager import agent_manager
from backend.apps.agents.core.models import AgentSession, Message


def p_seed(status: str) -> AgentSession:
    s = AgentSession(name="t", model="sonnet")
    s.status = status
    s.messages = [Message(role="user", content="hi"), Message(role="assistant", content="hello")]
    agent_manager.sessions[s.id] = s
    return s


@pytest.mark.asyncio
@pytest.mark.parametrize("terminal", ["completed", "error", "stopped"])
async def test_stopping_a_settled_chat_leaves_its_status_alone(terminal: str) -> None:
    s = p_seed(terminal)
    try:
        await agent_manager.stop_agent(s.id)
        assert s.status == terminal, "a restart must not relabel a finished conversation"
        assert s.needs_fresh_session is False, "nothing was interrupted, so nothing needs rebuilding"
        assert s.closed_at is None
    finally:
        agent_manager.sessions.pop(s.id, None)
        agent_manager.tasks.pop(s.id, None)


@pytest.mark.asyncio
@pytest.mark.parametrize("live", ["running", "waiting_approval"])
async def test_stopping_a_live_turn_still_stops_it(live: str) -> None:
    """The discriminating half: the Stop button must keep working."""
    s = p_seed(live)
    try:
        await agent_manager.stop_agent(s.id)
        assert s.status == "stopped"
        assert s.needs_fresh_session is True
        assert s.closed_at is not None
    finally:
        agent_manager.sessions.pop(s.id, None)
        agent_manager.tasks.pop(s.id, None)
