"""Boot restore must never destroy the durable copy of a session.

restore_all_sessions used to unlink every open session's JSON file after loading
it into memory, making RAM the ONLY copy; any non-graceful shutdown (updater
SIGKILL, crash, power loss) then wiped the chat permanently. This pins the
invariant: restoring an open session loads it into memory AND leaves its file on
disk, while closed sessions stay on disk untouched and out of memory.

Run with:  backend/.venv/bin/python -m pytest backend/tests/test_session_restore_durability.py
"""
import asyncio
import os
from datetime import datetime

from pytest import MonkeyPatch

from backend.apps.agents import agent_manager as am
from backend.apps.agents.core.models import AgentSession
from backend.apps.agents.manager.session.session_store import save_session


def p_session_path(sessions_dir: str, session_id: str) -> str:
    return os.path.join(sessions_dir, f"{session_id}.json")


def test_restore_keeps_open_session_file_on_disk(tmp_path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(am, "SESSIONS_DIR", str(tmp_path))
    mgr = am.AgentManager()
    session = AgentSession(name="open chat", model="sonnet")
    assert session.closed_at is None
    save_session(session.id, session.model_dump(mode="json"))

    asyncio.run(mgr.restore_all_sessions())

    assert session.id in mgr.sessions
    assert os.path.exists(p_session_path(str(tmp_path), session.id)), (
        "restore must not unlink the durable session file; memory-only sessions "
        "are lost on any non-graceful shutdown"
    )


def test_restore_skips_closed_sessions_but_keeps_their_files(tmp_path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(am, "SESSIONS_DIR", str(tmp_path))
    mgr = am.AgentManager()
    closed = AgentSession(name="closed chat", model="sonnet", closed_at=datetime.now())
    save_session(closed.id, closed.model_dump(mode="json"))

    asyncio.run(mgr.restore_all_sessions())

    assert closed.id not in mgr.sessions
    assert os.path.exists(p_session_path(str(tmp_path), closed.id))


def test_restore_settles_stale_running_status(tmp_path, monkeypatch: MonkeyPatch) -> None:
    # The app died mid-turn: restore settles the status, and the file still survives.
    monkeypatch.setattr(am, "SESSIONS_DIR", str(tmp_path))
    mgr = am.AgentManager()
    session = AgentSession(name="mid turn", model="sonnet", status="running")
    save_session(session.id, session.model_dump(mode="json"))

    asyncio.run(mgr.restore_all_sessions())

    assert mgr.sessions[session.id].status in ("completed", "stopped")
    assert os.path.exists(p_session_path(str(tmp_path), session.id))
