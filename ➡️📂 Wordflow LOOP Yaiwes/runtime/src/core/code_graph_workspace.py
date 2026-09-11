"""Anchored deterministic CODE GRAPH contract for Wordflow LOOP Yaiwes.

This module is not an orchestrator. It defines and serializes the graph used by
CODE_GRAPH_ARCHITECTURE_PROGRAMMING_LOOP and projects task dependencies into the
existing DAGEngine manifest contract.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Dict, List, Literal, Mapping, Sequence

NodeKind = Literal[
    "source_file", "requirement", "capability", "task", "placement", "agent",
    "sandbox", "test", "evidence", "deployment", "gap", "checkpoint", "state",
]
EdgeKind = Literal[
    "extracts", "requires", "implements", "depends_on", "placed_at", "owned_by",
    "reviewed_by", "executes_in", "validated_by", "produces", "promotes_to",
    "tracks", "checkpoint_of", "state_of",
]
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
NODE_KINDS = {
    "source_file", "requirement", "capability", "task", "placement", "agent",
    "sandbox", "test", "evidence", "deployment", "gap", "checkpoint", "state",
}
EDGE_KINDS = {
    "extracts", "requires", "implements", "depends_on", "placed_at", "owned_by",
    "reviewed_by", "executes_in", "validated_by", "produces", "promotes_to",
    "tracks", "checkpoint_of", "state_of",
}


class CodeGraphError(ValueError):
    """Fail-closed validation error for CODE GRAPH contracts."""


@dataclass(frozen=True)
class CodeGraphNode:
    node_id: str
    kind: NodeKind
    payload: Mapping[str, Any]


@dataclass(frozen=True)
class CodeGraphEdge:
    source: str
    target: str
    kind: EdgeKind


def _canonical_payload(value: Mapping[str, Any]) -> Dict[str, Any]:
    try:
        encoded = json.dumps(
            value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        )
        decoded = json.loads(encoded)
    except (TypeError, ValueError) as exc:
        raise CodeGraphError("payload must be JSON-serializable") from exc
    if not isinstance(decoded, dict):
        raise CodeGraphError("payload must serialize to object")
    return decoded


def build_code_graph(
    nodes: Sequence[CodeGraphNode],
    edges: Sequence[CodeGraphEdge],
    *,
    contract: str = "tel.workflow/v4",
) -> Dict[str, Any]:
    if contract != "tel.workflow/v4":
        raise CodeGraphError("unsupported contract")
    if not nodes:
        raise CodeGraphError("at least one node required")

    by_id: Dict[str, Dict[str, Any]] = {}
    for node in nodes:
        if not _ID.fullmatch(node.node_id):
            raise CodeGraphError("invalid node_id")
        if node.kind not in NODE_KINDS:
            raise CodeGraphError(f"invalid node kind: {node.kind}")
        if node.node_id in by_id:
            raise CodeGraphError(f"duplicate node_id: {node.node_id}")
        by_id[node.node_id] = {
            "kind": node.kind,
            "payload": _canonical_payload(node.payload),
        }

    canonical_edges: List[Dict[str, str]] = []
    seen = set()
    for edge in edges:
        if edge.kind not in EDGE_KINDS:
            raise CodeGraphError(f"invalid edge kind: {edge.kind}")
        if edge.source not in by_id or edge.target not in by_id:
            raise CodeGraphError("edge endpoint missing")
        if edge.source == edge.target:
            raise CodeGraphError("self-edge forbidden")
        key = (edge.source, edge.target, edge.kind)
        if key in seen:
            raise CodeGraphError("duplicate edge")
        seen.add(key)
        canonical_edges.append(
            {"source": edge.source, "target": edge.target, "kind": edge.kind}
        )

    canonical_edges.sort(key=lambda edge: (edge["source"], edge["target"], edge["kind"]))
    return {
        "contract": contract,
        "workspace": "wordflow_loop/code_graph",
        "nodes": {node_id: by_id[node_id] for node_id in sorted(by_id)},
        "edges": canonical_edges,
    }


def validate_code_graph(graph: Mapping[str, Any]) -> None:
    if graph.get("contract") != "tel.workflow/v4":
        raise CodeGraphError("invalid contract")
    if graph.get("workspace") != "wordflow_loop/code_graph":
        raise CodeGraphError("invalid workspace")
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, dict) or not nodes:
        raise CodeGraphError("nodes must be non-empty object")
    if not isinstance(edges, list):
        raise CodeGraphError("edges must be list")
    for node_id, spec in nodes.items():
        if not _ID.fullmatch(node_id) or not isinstance(spec, dict):
            raise CodeGraphError("invalid node entry")
        if spec.get("kind") not in NODE_KINDS or not isinstance(spec.get("payload"), dict):
            raise CodeGraphError("invalid node spec")
    seen = set()
    for edge in edges:
        if not isinstance(edge, dict):
            raise CodeGraphError("invalid edge entry")
        source, target, kind = edge.get("source"), edge.get("target"), edge.get("kind")
        if source not in nodes or target not in nodes or source == target or kind not in EDGE_KINDS:
            raise CodeGraphError("invalid edge")
        key = (source, target, kind)
        if key in seen:
            raise CodeGraphError("duplicate edge")
        seen.add(key)


def serialize_code_graph(graph: Mapping[str, Any]) -> str:
    validate_code_graph(graph)
    return json.dumps(graph, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def graph_sha256(graph: Mapping[str, Any]) -> str:
    return hashlib.sha256(serialize_code_graph(graph).encode("utf-8")).hexdigest()


def task_dependency_manifest(graph: Mapping[str, Any]) -> Dict[str, Any]:
    """Project task nodes + depends_on edges to the existing DAGEngine manifest."""
    validate_code_graph(graph)
    nodes = graph["nodes"]
    task_ids = {node_id for node_id, spec in nodes.items() if spec["kind"] == "task"}
    projected = {
        task_id: {"payload": nodes[task_id]["payload"], "depends_on": []}
        for task_id in sorted(task_ids)
    }
    for edge in graph["edges"]:
        if edge["kind"] != "depends_on":
            continue
        if edge["source"] not in task_ids or edge["target"] not in task_ids:
            raise CodeGraphError("depends_on edges must connect task nodes")
        projected[edge["source"]]["depends_on"].append(edge["target"])
    for spec in projected.values():
        spec["depends_on"].sort()
    if not projected:
        raise CodeGraphError("at least one task node required for DAG projection")
    return {"nodes": projected}
