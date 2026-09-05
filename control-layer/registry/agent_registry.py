"""Agent Registry + capability index.
SOURCE: Discovery → Schema → Sheriff → Registry → Router
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentEntry:
    id: str
    version: str
    capabilities: tuple[str, ...]
    recipe: str
    memory: dict[str, bool]
    permissions: dict[str, Any]
    path: str


@dataclass
class AgentRegistry:
    agents: dict[str, AgentEntry] = field(default_factory=dict)
    by_capability: dict[str, list[str]] = field(default_factory=dict)

    def register(self, entry: AgentEntry) -> None:
        self.agents[entry.id] = entry
        for cap in entry.capabilities:
            self.by_capability.setdefault(cap, [])
            if entry.id not in self.by_capability[cap]:
                self.by_capability[cap].append(entry.id)

    def resolve_by_capabilities(self, required: list[str]) -> list[str]:
        if not required:
            return list(self.agents.keys())
        sets = [set(self.by_capability.get(c, [])) for c in required]
        if not sets:
            return []
        hit = sets[0].intersection(*sets[1:]) if len(sets) > 1 else sets[0]
        return sorted(hit)

    def get(self, agent_id: str) -> AgentEntry | None:
        return self.agents.get(agent_id)
