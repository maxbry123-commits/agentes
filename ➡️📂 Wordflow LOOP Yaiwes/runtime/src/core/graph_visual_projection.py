"""Deterministic, renderer-agnostic projection of CODE GRAPH state."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping


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


def _seal(payload: Dict[str, Any]) -> Dict[str, Any]:
    unsigned = dict(payload)
    unsigned.pop("sha256", None)
    canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    payload["sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return payload


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
            "current": "renderer_agnostic_json",
            "enrichment_preference": "graphify",
            "graphify_runtime_verified": False,
            "graphology_required": False,
            "sigma_required": False,
            "core_dependency": False,
        },
    }
    return _seal(payload)


def _ref_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"


def build_crazy_wall_projection(
    task_nodes_document: Mapping[str, Any], checkpoint_document: Mapping[str, Any]
) -> Dict[str, Any]:
    """Project real Crazy Wall tasks, queue, GAPs, agents, evidence and checkpoint."""
    if task_nodes_document.get("schema") != "yaiwes.crazywall-dag/v1":
        raise VisualProjectionError("TASK_NODES_SCHEMA_INVALID")
    raw_tasks = task_nodes_document.get("nodes")
    if not isinstance(raw_tasks, list) or not raw_tasks:
        raise VisualProjectionError("TASK_NODES_REQUIRED")
    checkpoint_id = checkpoint_document.get("checkpoint_id")
    if not isinstance(checkpoint_id, str) or not checkpoint_id.strip():
        raise VisualProjectionError("CHECKPOINT_ID_REQUIRED")

    task_ids = {str(task.get("id", "")).strip() for task in raw_tasks}
    if "" in task_ids or len(task_ids) != len(raw_tasks):
        raise VisualProjectionError("TASK_ID_INVALID_OR_DUPLICATE")

    nodes = []
    edges = []
    queue = []
    agents = set()
    gaps = set()
    evidence_refs = set()
    for task in raw_tasks:
        task_id = str(task["id"])
        status = str(task.get("status", "UNKNOWN"))
        owner = str(task.get("claimed_by") or "")
        nodes.append(VisualNode(task_id, str(task.get("task") or task_id), "task", status, owner, group="tasks"))
        if status != "PASS":
            queue.append({"id": task_id, "status": status, "owner": owner})
        if owner:
            agents.add(owner)
            edges.append(VisualEdge(f"agent:{owner}", task_id, "owns"))
        for dependency in task.get("depends_on", []):
            if dependency not in task_ids:
                raise VisualProjectionError("TASK_DEPENDENCY_MISSING")
            edges.append(VisualEdge(str(dependency), task_id, "unblocks"))
        for gap in task.get("gaps", []):
            gap = str(gap).strip()
            if gap:
                gaps.add(gap)
                edges.append(VisualEdge(_ref_id("gap", gap), task_id, "reported_for"))
        for reference in task.get("evidence", []):
            reference = str(reference).strip()
            if reference:
                evidence_refs.add(reference)
                edges.append(VisualEdge(task_id, _ref_id("evidence", reference), "has_evidence"))

    nodes.extend(VisualNode(f"agent:{owner}", owner, "agent", "ASSIGNED", owner, group="agents") for owner in agents)
    nodes.extend(VisualNode(_ref_id("gap", gap), gap, "gap", "RECORDED", group="gaps") for gap in gaps)
    nodes.extend(
        VisualNode(_ref_id("evidence", ref), ref, "evidence", "RECORDED", group="evidence")
        for ref in evidence_refs
    )
    nodes.append(
        VisualNode(
            f"checkpoint:{checkpoint_id}",
            checkpoint_id,
            "checkpoint",
            str(checkpoint_document.get("status", "UNKNOWN")),
            str(checkpoint_document.get("claimed_by") or ""),
            group="checkpoints",
        )
    )

    payload = build_visual_projection(nodes, edges)
    payload["source_contracts"] = ["yaiwes.crazywall-dag/v1", "tel.workflow/v4"]
    payload["queue"] = sorted(queue, key=lambda item: (item["status"], item["id"]))
    payload["panels"] = {
        "tasks": len(raw_tasks),
        "queue": len(queue),
        "gaps": len(gaps),
        "agents": len(agents),
        "evidence": len(evidence_refs),
        "checkpoints": 1,
    }
    return _seal(payload)
