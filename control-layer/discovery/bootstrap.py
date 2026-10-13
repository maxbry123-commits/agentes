"""Bootstrap proyecto: Discovery → Schema/Sheriff → Registry.
SOURCE: nodes/*.yaml → Agent Registry sin capa por agente.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any

from .agent_discovery import discover_agents
from registry.agent_registry import AgentRegistry, AgentEntry
from sheriff.agent_validate import validate_agent


def bootstrap_agents(project_root: str | Path, project_id: str = "") -> dict[str, Any]:
    discovered = discover_agents(project_root)
    registry = AgentRegistry()
    rejected: list[dict[str, Any]] = []
    accepted: list[str] = []

    for d in discovered:
        v = validate_agent(d.data, project_id=project_id or None)
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
        registry.register(entry)
        accepted.append(entry.id)

    return {
        "accepted": accepted,
        "rejected": rejected,
        "registry_size": len(registry.agents),
        "capabilities_index": {k: v for k, v in registry.by_capability.items()},
        "registry": registry,
    }
