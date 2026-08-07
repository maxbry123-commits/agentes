"""Placement Engine."""
from __future__ import annotations
from dataclasses import asdict, dataclass

DOMAIN_MAP = (("code.", "cognitive/code"), ("reason.", "cognitive/reasoning"), ("analyze.", "cognitive/analysis"), ("git.", "execution/git"), ("fs.", "execution/filesystem"), ("filesystem.", "execution/filesystem"), ("terminal.", "execution/terminal"), ("browser.", "execution/browser"), ("workflow.", "orchestration/workflow"), ("schedule.", "orchestration/scheduler"), ("memory.", "memory"), ("graph.", "memory/graph"), ("api.", "connectivity/api"), ("mcp.", "connectivity/mcp"), ("dataset.", "data/datasets"), ("knowledge.", "data/knowledge"))

@dataclass
class Placement:
    domain: str
    path: str
    namespace: str
    capability_id: str
    def to_dict(self): return asdict(self)

def resolve_placement(capability_id, plugin_id):
    domain = "integrations"
    cid = capability_id.lower()
    for prefix, dom in DOMAIN_MAP:
        if cid.startswith(prefix) or prefix.rstrip(".") in cid:
            domain = dom; break
    return Placement(domain, f"extensions/{domain}/{plugin_id}", domain.replace("/", "."), capability_id)
