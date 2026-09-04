"""Placement Engine · dónde vive la extensión (no el path del repo fuente)."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

# Taxonomía de extensiones (runtime, no source store)
DOMAIN_MAP = {
    "code.": "cognitive/code",
    "reason.": "cognitive/reasoning",
    "analyze.": "cognitive/analysis",
    "git.": "execution/git",
    "fs.": "execution/filesystem",
    "filesystem.": "execution/filesystem",
    "terminal.": "execution/terminal",
    "browser.": "execution/browser",
    "workflow.": "orchestration/workflow",
    "schedule.": "orchestration/scheduler",
    "parallel.": "orchestration/parallel",
    "memory.": "memory",
    "graph.": "memory/graph",
    "api.": "connectivity/api",
    "mcp.": "connectivity/mcp",
    "device.": "connectivity/devices",
    "dataset.": "data/datasets",
    "knowledge.": "data/knowledge",
}


@dataclass
class Placement:
    domain: str
    path: str
    namespace: str
    capability_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_placement(capability_id: str, plugin_id: str) -> Placement:
    domain = "integrations"
    for prefix, dom in DOMAIN_MAP.items():
        if capability_id.startswith(prefix) or prefix.rstrip(".") in capability_id:
            domain = dom
            break
    path = f"extensions/{domain}/{plugin_id}"
    namespace = domain.replace("/", ".")
    return Placement(domain=domain, path=path, namespace=namespace, capability_id=capability_id)
