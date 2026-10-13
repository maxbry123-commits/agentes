from dataclasses import dataclass, field
from typing import Mapping, Sequence

from .enums import NodeStatus


@dataclass(frozen=True)
class Goal:
    goal_id: str
    description: str
    priority: int = 50
    required: bool = True


@dataclass(frozen=True)
class NodeDefinition:
    node_id: str
    name: str
    role: str
    dependencies: tuple[str, ...] = ()
    priority: int = 50
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class NodeRuntime:
    node_id: str
    status: NodeStatus = NodeStatus.PENDING
    attempts: int = 0
    last_error: str | None = None


@dataclass(frozen=True)
class WorkflowDefinition:
    workflow_id: str
    name: str
    group: str
    goals: tuple[Goal, ...]
    nodes: tuple[NodeDefinition, ...]
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Failure:
    failure_type: str
    detail: str
    retryable: bool
    evidence: tuple[str, ...] = ()
    affected_node: str | None = None


@dataclass(frozen=True)
class ChangeProposal:
    proposal_id: str
    source: str
    description: str
    affected_nodes: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class Checkpoint:
    workflow_id: str
    sequence: int
    state_version: int
    state_hash: str
