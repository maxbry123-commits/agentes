"""W07 · Agent Registry · capability-based, no name lock."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class AgentManifest:
    id: str
    name: str
    capabilities: list[str]
    group: str = "general"  # frontend|backend|research|general
    cost_weight: float = 1.0
    priority: int = 100
    healthy: bool = True
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AgentRegistry:
    def __init__(self) -> None:
        self._by_id: Dict[str, AgentManifest] = {}

    def register(self, manifest: AgentManifest | dict) -> AgentManifest:
        m = manifest if isinstance(manifest, AgentManifest) else AgentManifest(
            id=str(manifest["id"]),
            name=str(manifest.get("name") or manifest["id"]),
            capabilities=list(manifest.get("capabilities") or []),
            group=str(manifest.get("group") or "general"),
            cost_weight=float(manifest.get("cost_weight") or 1.0),
            priority=int(manifest.get("priority") or 100),
            healthy=bool(manifest.get("healthy", True)),
            meta=dict(manifest.get("meta") or {}),
        )
        if not m.capabilities:
            raise ValueError("capabilities_required")
        self._by_id[m.id] = m
        return m

    def resolve(self, capability: str, *, group: str | None = None) -> list[AgentManifest]:
        out = []
        for m in self._by_id.values():
            if not m.healthy:
                continue
            if capability not in m.capabilities:
                continue
            if group and m.group != group:
                continue
            out.append(m)
        out.sort(key=lambda x: (x.priority, x.cost_weight))
        return out

    def get(self, agent_id: str) -> AgentManifest | None:
        return self._by_id.get(agent_id)

    def list_all(self) -> list[AgentManifest]:
        return list(self._by_id.values())
