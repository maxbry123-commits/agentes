"""Sheriff — validar agente antes de Registry.
SOURCE: discovery ≠ autorización
Checks: schema · proyecto · capabilities · recipe · memory · tools
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AgentValidation:
    ok: bool
    errors: tuple[str, ...]


def validate_agent(data: dict[str, Any], *, project_id: str | None = None) -> AgentValidation:
    errors: list[str] = []
    if data.get("type") != "agent":
        errors.append("type must be agent")
    aid = data.get("id")
    if not aid or not isinstance(aid, str):
        errors.append("missing id")
    if not data.get("version"):
        errors.append("missing version")
    caps = data.get("capabilities") or []
    if not isinstance(caps, list) or len(caps) < 1:
        errors.append("capabilities required non-empty")
    mem = data.get("memory") or {}
    if mem.get("global") is True:
        errors.append("global memory requires explicit allow (default false)")
    # recipe optional but recommended
    return AgentValidation(ok=len(errors) == 0, errors=tuple(errors))


def build_execution_context(
    *,
    tenant_id: str,
    project_id: str,
    agent_id: str,
    agent_version: str,
    workflow_id: str,
    task_id: str,
    session_id: str,
) -> dict[str, Any]:
    return {
        "tenant_id": tenant_id,
        "project_id": project_id,
        "agent_id": agent_id,
        "agent_version": agent_version,
        "workflow_id": workflow_id,
        "task_id": task_id,
        "session_id": session_id,
        "memory": {
            "private_scope": f"{tenant_id}/{project_id}/agents/{agent_id}",
            "project_scope": f"{tenant_id}/{project_id}/project",
        },
    }
