"""Capability Graph · requires/provides multi-hop."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any

@dataclass
class CapNode:
    id: str
    requires: list = field(default_factory=list)
    provides: list = field(default_factory=list)
    plugin_id: str = ""
    def to_dict(self): return asdict(self)

class CapabilityGraph:
    def __init__(self):
        self.nodes = {}
    def add(self, node: CapNode):
        self.nodes[node.id] = node
    def add_from_contract(self, contract, plugin_id=""):
        cid = str(contract.get("id") or "")
        if not cid: return
        self.add(CapNode(cid, list(contract.get("requires") or []), list(contract.get("provides") or [cid]), plugin_id or str(contract.get("owner_plugin") or "")))
    def resolve_chain(self, capability_id, max_depth=8):
        ordered, seen = [], set()
        def visit(cid, depth):
            if cid in seen or depth > max_depth: return
            seen.add(cid)
            node = self.nodes.get(cid)
            if node:
                for req in node.requires: visit(req, depth+1)
            ordered.append(cid)
        visit(capability_id, 0)
        return ordered
    def to_dict(self):
        return {k: v.to_dict() for k,v in self.nodes.items()}
