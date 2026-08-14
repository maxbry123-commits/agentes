# -*- coding: utf-8 -*-
"""RemoteWorkerRouter — D5. Assign tasks to local|ssh|docker. 0% LLM."""
from __future__ import annotations

from typing import Any

from .docker_transport import DockerTransport, FakeDockerTransport
from .ssh_orchestrator import FakeSSHTransport, SSHOrchestrator, SSHTransport


class RemoteWorkerRouter:
    def __init__(
        self,
        *,
        ssh: SSHOrchestrator | None = None,
        docker: DockerTransport | None = None,
        allow_real: bool = False,
    ):
        if allow_real:
            raise RuntimeError("REAL_REMOTE_DISABLED until infra wave")
        self.ssh = ssh or SSHOrchestrator(transport=FakeSSHTransport())
        self.docker = docker or FakeDockerTransport()

    def route(
        self,
        task_id: str,
        *,
        mode: str = "local",
        command: str = "true",
        host: str | None = None,
        image: str | None = None,
    ) -> dict[str, Any]:
        m = (mode or "local").lower()
        if m == "local":
            return {
                "ok": True,
                "mode": "local",
                "task_id": task_id,
                "command": command,
            }
        if m == "ssh":
            if not host:
                return {"ok": False, "reason": "HOST_REQUIRED", "mode": "ssh"}
            r = self.ssh.run_remote(host, command)
            r["task_id"] = task_id
            r["mode"] = "ssh"
            return r
        if m == "docker":
            img = image or "python:3.11-slim"
            c = self.docker.create(img, name=f"wf_{task_id}")
            try:
                ex = self.docker.exec(c["container_id"], command)
            finally:
                self.docker.remove(c["container_id"])
            return {
                "ok": ex.get("exit_code", 1) == 0,
                "mode": "docker",
                "task_id": task_id,
                "container_id": c["container_id"],
                "result": ex,
            }
        return {"ok": False, "reason": f"UNKNOWN_MODE_{m}"}
