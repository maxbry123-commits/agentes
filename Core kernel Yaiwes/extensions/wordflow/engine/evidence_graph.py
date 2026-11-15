# -*- coding: utf-8 -*-
"""EvidenceGraph — T27. Minimal nodes+edges. 0% LLM."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hash_payload(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class EvidenceGraph:
    """Append-only evidence DAG fragment (in-memory)."""

    def __init__(self, *,
                 mission_id: str | None = None):
        self.mission_id = mission_id
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: list[dict[str, str]] = []  # {from, to, rel}

    def add_node(
        self,
        kind: str,
        payload: Any,
        *,
        ref_id: str | None = None,
        meta: dict[str, Any] | None = None,
        node_id: str | None = None,
    ) -> dict[str, Any]:
        nid = node_id or f"ev_{uuid.uuid4().hex[:12]}"
        node = {
            "node_id": nid,
            "kind": kind,
            "ref_id": ref_id,
            "created_at": _now(),
            "payload_hash": _hash_payload(payload),
            "meta": dict(meta or {}),
        }
        if self.mission_id:
            node["meta"]["mission_id"] = self.mission_id
        self.nodes[nid] = node
        return dict(node)

    def link(self, from_id: str, to_id: str, rel: str = "supports") -> dict[str, str]:
        if from_id not in self.nodes or to_id not in self.nodes:
            raise KeyError("both nodes must exist")
        edge = {"from": from_id, "to": to_id, "rel": rel}
        self.edges.append(edge)
        return dict(edge)

    def add_chain(
        self,
        items: list[tuple[str, Any]],
        *,
        rel: str = "next",
    ) -> list[str]:
        """items = [(kind, payload), ...] linked sequentially."""
        ids: list[str] = []
        prev: str | None = None
        for kind, payload in items:
            n = self.add_node(kind, payload)
            ids.append(n["node_id"])
            if prev is not None:
                self.link(prev, n["node_id"], rel=rel)
            prev = n["node_id"]
        return ids

    def snapshot(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "nodes": [dict(n) for n in self.nodes.values()],
            "edges": [dict(e) for e in self.edges],
        }

    def verify_node(self, node_id: str, payload: Any) -> bool:
        n = self.nodes.get(node_id)
        if not n:
            return False
        return n["payload_hash"] == _hash_payload(payload)
