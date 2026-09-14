"""Agent Discovery — scan nodes/*.yaml → candidatos.
SOURCE: proyecto declarativo · sin if agent == X
Descubrimiento ≠ autorización (Sheriff valida después).
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DiscoveredAgent:
    path: str
    data: dict[str, Any]


def discover_agents(project_root: str | Path) -> list[DiscoveredAgent]:
    root = Path(project_root)
    nodes = root / "nodes"
    if not nodes.is_dir():
        return []
    found: list[DiscoveredAgent] = []
    for p in sorted(nodes.glob("*.yaml")):
        try:
            import yaml
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        except Exception:
            data = {}
        found.append(DiscoveredAgent(path=str(p.relative_to(root)), data=data))
    return found
