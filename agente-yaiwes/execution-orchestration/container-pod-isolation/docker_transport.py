# -*- coding: utf-8 -*-
"""DockerTransport — D5. Protocol + Fake. No daemon required. 0% LLM."""
from __future__ import annotations

import uuid
from typing import Any, Protocol, runtime_checkable


class DockerError(Exception):
    def __init__(self, code: str, detail: str = ""):
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}" if detail else code)


@runtime_checkable
class DockerTransport(Protocol):
    def create(self, image: str, *,
               name: str | None = None,
               env: dict[str, str] | None = None) -> dict[str, Any]: ...

    def exec(self, container_id: str, command: str) -> dict[str, Any]: ...

    def remove(self, container_id: str) -> None: ...


class FakeDockerTransport:
    def __init__(self):
        self.containers: dict[str, dict[str, Any]] = {}
        self.history: list[dict[str, Any]] = []

    def create(self, image: str, *,
               name: str | None = None,
               env: dict[str, str] | None = None) -> dict[str, Any]:
        cid = f"ctr_{uuid.uuid4().hex[:10]}"
        meta = {
            "container_id": cid,
            "image": image,
            "name": name or cid,
            "env_keys": list((env or {}).keys()),
            "status": "CREATED",
        }
        self.containers[cid] = meta
        self.history.append({"op": "create", **meta})
        return dict(meta)

    def exec(self, container_id: str, command: str) -> dict[str, Any]:
        c = self.containers.get(container_id)
        if not c:
            raise DockerError("CONTAINER_NOT_FOUND", container_id)
        r = {
            "container_id": container_id,
            "command": command,
            "exit_code": 0,
            "stdout": f"fake-docker:{command}",
        }
        self.history.append({"op": "exec", **r})
        return r

    def remove(self, container_id: str) -> None:
        if container_id in self.containers:
            self.containers[container_id]["status"] = "REMOVED"
            self.history.append({"op": "remove", "container_id": container_id})
