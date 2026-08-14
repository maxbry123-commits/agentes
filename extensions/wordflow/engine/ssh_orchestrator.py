# -*- coding: utf-8 -*-
"""SSH Orchestrator — T20. Interface + Fake only. No network. 0% LLM."""
from __future__ import annotations

import uuid
from typing import Any, Protocol, runtime_checkable


class SSHError(Exception):
    def __init__(self, code: str, detail: str = ""):
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}" if detail else code)


@runtime_checkable
class SSHTransport(Protocol):
    def connect(self, host: str, *,
                port: int = 22,
                user: str = "root") -> dict[str, Any]: ...

    def exec(self, session_id: str, command: str) -> dict[str, Any]: ...

    def close(self, session_id: str) -> None: ...


class FakeSSHTransport:
    """In-memory fake — never opens sockets."""

    def __init__(self):
        self.sessions: dict[str, dict[str, Any]] = {}
        self.history: list[dict[str, Any]] = []

    def connect(self, host: str, *,
                port: int = 22,
                user: str = "root") -> dict[str, Any]:
        sid = f"ssh_{uuid.uuid4().hex[:10]}"
        sess = {
            "session_id": sid,
            "host": host,
            "port": port,
            "user": user,
            "status": "CONNECTED",
        }
        self.sessions[sid] = sess
        self.history.append({"op": "connect", **sess})
        return dict(sess)

    def exec(self, session_id: str, command: str) -> dict[str, Any]:
        sess = self.sessions.get(session_id)
        if sess is None or sess.get("status") != "CONNECTED":
            raise SSHError("SESSION_INVALID", session_id)
        result = {
            "session_id": session_id,
            "command": command,
            "exit_code": 0,
            "stdout": f"fake:{command}",
            "stderr": "",
        }
        self.history.append({"op": "exec", **result})
        return result

    def close(self, session_id: str) -> None:
        sess = self.sessions.get(session_id)
        if sess:
            sess["status"] = "CLOSED"
            self.history.append({"op": "close", "session_id": session_id})


class SSHOrchestrator:
    """Routes remote execution via transport. Default Fake."""

    def __init__(self, transport: SSHTransport | None = None, *,
                 allow_real: bool = False):
        if allow_real:
            raise SSHError(
                "REAL_SSH_DISABLED",
                "Real SSH deferred until post-Wordflow / infra wave",
            )
        self.transport: SSHTransport = transport or FakeSSHTransport()
        self.allow_real = False

    def run_remote(
        self,
        host: str,
        command: str,
        *,
        port: int = 22,
        user: str = "root",
    ) -> dict[str, Any]:
        sess = self.transport.connect(host, port=port, user=user)
        try:
            result = self.transport.exec(sess["session_id"], command)
        finally:
            self.transport.close(sess["session_id"])
        return {
            "ok": result.get("exit_code", 1) == 0,
            "host": host,
            "command": command,
            "result": result,
        }

    def migrate_task_stub(
        self,
        task_id: str,
        host: str,
        *,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        base = self.run_remote(host, f"wordflow-migrate {task_id}")
        base["task_id"] = task_id
        base["payload_keys"] = list((payload or {}).keys())
        base["mode"] = "stub"
        return base
