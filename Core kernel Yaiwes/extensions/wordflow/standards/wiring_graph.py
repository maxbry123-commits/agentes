"""WiringGraph mínimo desde connect_catalog + component_catalog."""
from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Any, Set
import json

WF = Path(__file__).resolve().parents[1]

class WiringGraph:
    def __init__(self):
        self.nodes: Set[str] = set()
        self.edges: List[Dict[str, str]] = []

    def load_catalogs(self) -> None:
        conn_path = WF / "connect_catalog.json"
        comp_path = WF / "component_catalog.json"
        if conn_path.exists():
            data = json.loads(conn_path.read_text(encoding="utf-8"))
            for c in data.get("connections", []):
                frm, to = c.get("from", ""), c.get("to", "")
                if frm and to:
                    self.nodes.add(frm)
                    self.nodes.add(to)
                    self.edges.append({"from": frm, "to": to, "type": c.get("type", "")})
        if comp_path.exists():
            data = json.loads(comp_path.read_text(encoding="utf-8"))
            for comp in data.get("components", []):
                cid = str(comp.get("id", ""))
                if cid:
                    self.nodes.add(cid)

    def orphans(self, required_ids: List[str]) -> List[str]:
        connected = {e["from"] for e in self.edges} | {e["to"] for e in self.edges}
        return [r for r in required_ids if r not in connected and r not in self.nodes]

    def summary(self) -> Dict[str, Any]:
        return {"nodes": len(self.nodes), "edges": len(self.edges), "edge_list": self.edges[:50]}
