"""DAG + Dependency DAG · minimal deterministic graph.

Nodes have id, op, depends_on, status, params.
next() = first PENDING with all deps DONE/SKIPPED.
Dependency DAG: child missions as depends_on on TaskQueue.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .schema import SCHEMA_VERSION, _utcnow

NODE_DONE = frozenset({"DONE", "SKIPPED"})


@dataclass
class DagNode:
    id: str
    op: str
    depends_on: list[str] = field(default_factory=list)
    status: str = "PENDING"  # PENDING|DONE|FAILED|SKIPPED|RETRYABLE
    params: dict[str, Any] = field(default_factory=dict)
    retries: int = 0
    max_retries: int = 3
    timeout_sec: float = 120.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "DagNode":
        return DagNode(
            id=str(d["id"]),
            op=str(d["op"]),
            depends_on=list(d.get("depends_on") or []),
            status=str(d.get("status") or "PENDING"),
            params=dict(d.get("params") or {}),
            retries=int(d.get("retries") or 0),
            max_retries=int(d.get("max_retries") or 3),
            timeout_sec=float(d.get("timeout_sec") or 120.0),
        )


@dataclass
class DAG:
    mission_id: str
    nodes: list[DagNode] = field(default_factory=list)
    schema_version: str = SCHEMA_VERSION
    updated_at: str = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "nodes": [n.to_dict() for n in self.nodes],
            "schema_version": self.schema_version,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "DAG":
        return DAG(
            mission_id=str(d["mission_id"]),
            nodes=[DagNode.from_dict(x) for x in (d.get("nodes") or [])],
            schema_version=str(d.get("schema_version") or SCHEMA_VERSION),
            updated_at=str(d.get("updated_at") or _utcnow()),
        )

    def by_id(self) -> dict[str, DagNode]:
        return {n.id: n for n in self.nodes}

    def next(self) -> DagNode | None:
        idx = self.by_id()
        for n in self.nodes:
            if n.status != "PENDING":
                continue
            if all(idx[d].status in NODE_DONE for d in n.depends_on if d in idx):
                # missing dep id → treat as blocking
                if any(d not in idx for d in n.depends_on):
                    continue
                return n
        return None

    def mark(self, node_id: str, status: str) -> None:
        for n in self.nodes:
            if n.id == node_id:
                n.status = status
                break
        self.updated_at = _utcnow()

    def all_terminal(self) -> bool:
        return all(n.status in NODE_DONE or n.status == "FAILED" for n in self.nodes)

    def has_failed(self) -> bool:
        return any(n.status == "FAILED" for n in self.nodes)


class DagStore:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.dir = self.root / "missions"
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, mission_id: str) -> Path:
        safe = mission_id.replace("/", "_").replace("..", "_")
        d = self.dir / safe
        d.mkdir(parents=True, exist_ok=True)
        return d / "dag.json"

    def save(self, dag: DAG) -> None:
        p = self._path(dag.mission_id)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(dag.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(p)

    def load(self, mission_id: str) -> DAG | None:
        p = self._path(mission_id)
        if not p.is_file():
            return None
        return DAG.from_dict(json.loads(p.read_text(encoding="utf-8")))


def build_acquire_dag(mission_id: str, *,
                      dry_run: bool = False,
                      dep_mission_ids: Iterable[str] | None = None) -> DAG:
    """Standard acquire pipeline as DAG. Dependencies = other missions first."""
    nodes: list[DagNode] = []
    # optional external mission deps encoded as gate node
    deps = list(dep_mission_ids or [])
    if deps:
        nodes.append(DagNode(id="deps", op="WAIT_DEPS", params={"missions": deps}))
        prev = ["deps"]
    else:
        prev = []

    def add(oid: str, op: str, **params: Any) -> None:
        nonlocal prev
        nodes.append(DagNode(id=oid, op=op, depends_on=list(prev), params=params))
        prev = [oid]

    add("investigate", "INVESTIGATE")
    add("plan", "PLAN")
    if dry_run:
        add("budget_estimate", "BUDGET_ESTIMATE")
        return DAG(mission_id=mission_id, nodes=nodes)

    add("download", "DOWNLOAD")
    add("verify", "VERIFY_SHA256")
    add("index", "TAR_INDEX")
    add("extract", "EXTRACT")
    add("install", "INSTALL")
    add("test", "TEST")
    add("verify_final", "VERIFY_FINAL")
    return DAG(mission_id=mission_id, nodes=nodes)


def build_dependency_missions(
    parent_id: str,
    deps: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Describe child missions for TaskQueue (npm/pip/etc as separate missions).

    deps items: {id, repo?, kind, priority?}
    """
    out = []
    for d in deps:
        cid = str(d.get("id") or d.get("name") or "dep")
        out.append({
            "mission_id": f"{parent_id}__dep__{cid}",
            "repo": d.get("repo") or "",
            "kind": d.get("kind") or "runtime",
            "priority": int(d.get("priority") or 50),
            "depends_on": [],
            "parent": parent_id,
        })
    return out
