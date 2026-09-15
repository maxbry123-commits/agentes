from __future__ import annotations

from dataclasses import dataclass, field

from schemas.base import new_id, utc_now


@dataclass(slots=True)
class ExperimentNode:
    node_id: str = field(default_factory=lambda: new_id("expnode"))
    experiment_id: str = ""
    parent_id: str = ""
    hypothesis: str = ""
    patch_scope: str = ""
    result: dict = field(default_factory=dict)
    decision: dict = field(default_factory=dict)
    children_ids: list[str] = field(default_factory=list)
    status: str = "pending"
    depth: int = 0
    created_at: str = field(default_factory=utc_now)


@dataclass(slots=True)
class ExperimentBranch:
    branch_id: str = field(default_factory=lambda: new_id("branch"))
    root_id: str = ""
    nodes: list[ExperimentNode] = field(default_factory=list)
    status: str = "active"
    max_depth: int = 2
    max_active_nodes: int = 3
