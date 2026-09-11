"""Deterministic projection of CODE GRAPH state for visual renderers.

The output is renderer-agnostic JSON. Graphology/Sigma may consume it later,
but the Python core has no JS/runtime dependency.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Tuple


@dataclass(frozen=True)
class VisualNode:
    node_id: str
    label: str
    node_type: str
    status: str
    owner: str = ""
    priority: int = 0
    group: str = ""


@dataclass(frozen=True)
class VisualEdge:
    source: str
    target: str
    edge_type: str


class VisualProjectionError(ValueError):
    pass


def build_visual_projection(
    nodes: Iterable[VisualNode], edges: Iterable[VisualEdge]
) -> Dict[str, Any]:
    node_list = list(nodes)
    edge_list = list(edges)
    ids = [node.node_id for node in node_list]
    if any(not node_id.strip() for node_id in ids):
        raise VisualProjectionError("NODE_ID_REQUIRED")
    if len(ids) != len(set(ids)):
        raise VisualProjectionError("DUPLICATE_NODE_ID")
    known = set(ids)
    for edge in edge_list:
        if edge.source not in known or edge.target not in known:
            raise VisualProjectionError("EDGE_ENDPOINT_MISSING")

    projected_nodes = [
        {
            "id": node.node_id,
            "label": node.label or node.node_id,
            "type": node.node_type,
            "status": node.status,
            "owner": node.owner,
            "priority": node.priority,
            "group": node.group,
        }
        for node in sorted(node_list, key=lambda item: item.node_id)
    ]
    projected_edges = [
        {
            "id": f"{edge.source}->{edge.target}:{edge.edge_type}",
            "source": edge.source,
            "target": edge.target,
            "type": edge.edge_type,
        }
        for edge in sorted(edge_list, key=lambda item: (item.source, item.target, item.edge_type))
    ]
    payload = {
        "schema": "yaiwes.visual_graph/v1",
        "nodes": projected_nodes,
        "edges": projected_edges,
        "renderer_contract": {
            "preferred": "graphology+sigma",
            "required": False,
            "core_dependency": False,
        },
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    payload["sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return payload
