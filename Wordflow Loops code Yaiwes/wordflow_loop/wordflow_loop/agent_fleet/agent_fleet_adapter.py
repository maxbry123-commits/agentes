"""Deterministic agent-fleet binding for Wordflow LOOP YAIWES.

STEP2 wiring only. Runtime execution is intentionally fail-closed until STEP3
verifies the configured transport for each agent.
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class AgentBindingError(RuntimeError):
    """Raised when a binding cannot be resolved safely."""


@dataclass(frozen=True)
class AgentBinding:
    agent_id: str
    roles: tuple[str, ...]
    transport: str
    status: str
    command_env: str | None = None
    url_env: str | None = None
    token_env: str | None = None


class AgentFleetAdapter:
    """Loads a static fleet registry and routes by exact id/role.

    No model decides routing. Selection is deterministic: explicit agent id wins;
    otherwise the first registry slot declaring the requested role is selected.
    """

    def __init__(
        self,
        registry_path: str | Path | None = None,
        memory_root: str | Path | None = None,
    ) -> None:
        default = Path(__file__).with_name("agent_fleet_registry.json")
        self.registry_path = Path(registry_path) if registry_path else default
        self.memory_root = Path(memory_root) if memory_root else Path(__file__).with_name("memory")
        payload = json.loads(self.registry_path.read_text(encoding="utf-8"))
        self.contract = payload.get("contract")
        if self.contract != "tel.workflow/v4":
            raise AgentBindingError("REGISTRY_CONTRACT_MISMATCH")
        entries = payload.get("agents")
        if not isinstance(entries, list) or not entries:
            raise AgentBindingError("EMPTY_AGENT_REGISTRY")
        self._raw = entries
        self._by_id = {item["agent_id"]: item for item in entries}
        if len(self._by_id) != len(entries):
            raise AgentBindingError("DUPLICATE_AGENT_ID")

    def list_agents(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self._raw]

    def build_invocation_payload(self, agent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Inject the selected agent memory before its task contract."""
        if not isinstance(payload, dict) or not payload:
            raise AgentBindingError("NON_EMPTY_TASK_PAYLOAD_REQUIRED")
        self.resolve(agent_id=agent_id)
        try:
            from runtime.src.core.agent_memory_loader import (
                AgentMemoryError,
                build_pre_execution_context,
                load_agent_memory,
            )
        except (ImportError, ModuleNotFoundError) as exc:
            raise AgentBindingError("MEMORY_LOADER_UNAVAILABLE") from exc
        try:
            memory = load_agent_memory(self.memory_root, agent_id)
            task_contract = json.dumps(
                payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            context = build_pre_execution_context(memory, task_contract)
        except AgentMemoryError as exc:
            raise AgentBindingError(f"MEMORY_PREINJECTION_FAILED:{agent_id}:{exc}") from exc
        return {
            "agent_id": agent_id,
            "memory_sha256": memory.sha256,
            "pre_execution_context": context,
            "task_payload": dict(payload),
        }

    def resolve(self, *, agent_id: str | None = None, role: str | None = None) -> dict[str, Any]:
        if agent_id:
            item = self._by_id.get(agent_id)
            if item is None:
                raise AgentBindingError(f"UNKNOWN_AGENT:{agent_id}")
            return dict(item)
        if role:
            for item in sorted(self._raw, key=lambda value: int(value["slot"])):
                if role in item.get("roles", []):
                    return dict(item)
            raise AgentBindingError(f"NO_AGENT_FOR_ROLE:{role}")
        raise AgentBindingError("AGENT_ID_OR_ROLE_REQUIRED")

    def health_descriptor(self, agent_id: str) -> dict[str, Any]:
        item = self.resolve(agent_id=agent_id)
        transport = item.get("transport")
        configured = False
        if transport == "command_env":
            configured = bool(os.environ.get(item.get("command_env", "")))
        elif transport == "http_env":
            configured = bool(os.environ.get(item.get("url_env", "")))
        elif transport == "existing_adapter":
            configured = True
        return {
            "agent_id": agent_id,
            "wired": True,
            "step2_status": item.get("status"),
            "transport": transport,
            "runtime_configured": configured,
            "fail_closed": True,
        }

    def invoke(self, agent_id: str, payload: dict[str, Any], timeout_s: int = 120) -> dict[str, Any]:
        """Invoke only a runtime explicitly configured by environment.

        STEP2 never calls this method. STEP3 owns execution verification.
        """
        item = self.resolve(agent_id=agent_id)
        prepared_payload = self.build_invocation_payload(agent_id, payload)
        transport = item.get("transport")
        if transport == "command_env":
            env_name = item.get("command_env")
            raw = os.environ.get(env_name or "")
            if not raw:
                raise AgentBindingError(f"RUNTIME_UNAVAILABLE:{agent_id}:{env_name}")
            proc = subprocess.run(
                [*shlex.split(raw)],
                input=json.dumps(prepared_payload),
                text=True,
                capture_output=True,
                timeout=timeout_s,
                check=False,
            )
            if proc.returncode != 0:
                raise AgentBindingError(f"AGENT_COMMAND_FAILED:{agent_id}:{proc.returncode}")
            return {"agent_id": agent_id, "stdout": proc.stdout, "stderr": proc.stderr, "exit_code": 0}
        if transport == "http_env":
            url = os.environ.get(item.get("url_env", ""))
            if not url:
                raise AgentBindingError(f"RUNTIME_UNAVAILABLE:{agent_id}:url")
            headers = {"Content-Type": "application/json"}
            token_env = item.get("token_env")
            token = os.environ.get(token_env or "") if token_env else None
            if token:
                headers["Authorization"] = f"Bearer {token}"
            req = urllib.request.Request(
                url,
                data=json.dumps(prepared_payload).encode(),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout_s) as response:  # nosec B310 - URL is operator-configured
                body = response.read().decode()
            return {"agent_id": agent_id, "status": response.status, "body": body}
        if transport == "existing_adapter":
            raise AgentBindingError(f"DELEGATE_TO_EXISTING_ADAPTER:{agent_id}:{item.get('adapter_ref')}")
        raise AgentBindingError(f"UNSUPPORTED_TRANSPORT:{agent_id}:{transport}")
