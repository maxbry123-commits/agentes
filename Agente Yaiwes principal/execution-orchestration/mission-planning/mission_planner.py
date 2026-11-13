# -*- coding: utf-8 -*-
"""C-21 Mission Planner — Council decides; Planner divides into TaskGraph. 0% LLM."""
from __future__ import annotations

import hashlib
import json
from typing import Any


class TaskGraphError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def _node_id(prefix: str, index: int) -> str:
    return f"{prefix}_{index:02d}"


def _hash_graph(nodes: list[dict[str, Any]], edges: list[dict[str, str]]) -> str:
    canonical = json.dumps({"nodes": nodes, "edges": edges}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def plan_from_council(council_contract: dict[str, Any] | None) -> dict[str, Any]:
    """Build TaskGraph from CouncilContract.

    Expected council keys (soft):
      plan: list[str] | list[dict]  — ordered steps
      roles: list[str] (optional)
      risks: list[str] (optional)
      mission_id / lock_id (optional)
    """
    if not isinstance(council_contract, dict):
        raise TaskGraphError("COUNCIL_NOT_OBJECT", type(council_contract).__name__)

    raw_plan = council_contract.get("plan") or council_contract.get("tasks") or []
    if not isinstance(raw_plan, list) or len(raw_plan) == 0:
        raise TaskGraphError("COUNCIL_PLAN_EMPTY", "plan/tasks required")

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []
    prev_id: str | None = None

    for i, step in enumerate(raw_plan):
        nid = _node_id("T", i)
        if isinstance(step, str):
            title = step.strip() or f"step_{i}"
            meta: dict[str, Any] = {}
        elif isinstance(step, dict):
            title = str(step.get("title") or step.get("id") or f"step_{i}")
            meta = {k: v for k, v in step.items() if k not in ("title", "id")}
        else:
            raise TaskGraphError("COUNCIL_STEP_INVALID", f"index={i}")

        node = {
            "id": nid,
            "title": title,
            "status": "PENDING",
            "depends_on": [prev_id] if prev_id else [],
            "meta": meta,
        }
        nodes.append(node)
        if prev_id:
            edges.append({"from": prev_id, "to": nid})
        prev_id = nid

    graph_hash = _hash_graph(nodes, edges)
    mission_id = council_contract.get("mission_id") or council_contract.get("lock_id") or ""

    return {
        "ok": True,
        "mission_id": mission_id,
        "graph_id": f"tg_{graph_hash[:12]}",
        "graph_hash": graph_hash,
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "roles": list(council_contract.get("roles") or []),
        "risks": list(council_contract.get("risks") or []),
        "policies": dict(council_contract.get("policies") or {}),
        "llm_control": "DENY",
    }
