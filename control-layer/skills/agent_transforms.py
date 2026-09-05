"""Skills/transforms deterministas para D3 agents.
SOURCE: agent.schema · Discovery pipeline 0% LLM
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from sheriff.agent_validate import validate_agent, AgentValidation
from discovery.agent_discovery import discover_agents
from registry.agent_registry import AgentRegistry, AgentEntry


@dataclass(frozen=True)
class BootstrapResult:
    ok: bool
    accepted: tuple[str, ...]
    rejected: tuple[dict[str, Any], ...]
    capabilities: tuple[str, ...]


def transform_discovered_to_registry(project_root: str, project_id: str = "") -> BootstrapResult:
    discovered = discover_agents(project_root)
    reg = AgentRegistry()
    accepted: list[str] = []
    rejected: list[dict[str, Any]] = []
    for d in discovered:
        v: AgentValidation = validate_agent(d.data, project_id=project_id or None)
        if not v.ok:
            rejected.append({"path": d.path, "errors": list(v.errors)})
            continue
        entry = AgentEntry(
            id=str(d.data["id"]),
            version=str(d.data.get("version", "0.0.0")),
            capabilities=tuple(d.data.get("capabilities") or ()),
            recipe=str((d.data.get("workflow") or {}).get("recipe") or ""),
            memory=dict(d.data.get("memory") or {}),
            permissions=dict(d.data.get("permissions") or {}),
            path=d.path,
        )
        reg.register(entry)
        accepted.append(entry.id)
    caps = tuple(sorted(reg.by_capability.keys()))
    return BootstrapResult(
        ok=len(rejected) == 0 and len(accepted) > 0,
        accepted=tuple(accepted),
        rejected=tuple(rejected),
        capabilities=caps,
    )
