# G1 · NÚCLEO DETERMINISTA — Documento 2/4
**Bloques B3 (Nodos/Contratos) + B4 (DAG/Máquina de Estados) · UOOS Parte 1**
Fuente: `arquitectura_Wordflow.md`, Salida 1/13, líneas 77-509, literal

---

## B3 · enums.py + errors.py + contracts.py

```python
from enum import Enum


class WorkflowStatus(str, Enum):
    CREATED = "created"
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"
    PAUSED = "paused"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NodeStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class EventType(str, Enum):
    WORKFLOW_CREATED = "workflow.created"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_PAUSED = "workflow.paused"
    WORKFLOW_RESUMED = "workflow.resumed"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"

    NODE_CREATED = "node.created"
    NODE_STARTED = "node.started"
    NODE_PASSED = "node.passed"
    NODE_FAILED = "node.failed"

    CHECKPOINT_CREATED = "checkpoint.created"
    RECOVERY_STARTED = "recovery.started"

    CHANGE_PROPOSED = "change.proposed"
    DAG_PATCHED = "dag.patched"
```

```python
class WorkflowError(Exception):
    """Base error for deterministic workflow operations."""


class InvalidTransitionError(WorkflowError):
    """Raised when a state transition is not allowed."""


class ContractViolationError(WorkflowError):
    """Raised when a workflow contract is invalid."""


class DuplicateEventError(WorkflowError):
    """Raised when an event with an existing ID is inserted."""


class VersionConflictError(WorkflowError):
    """Raised when optimistic state versioning detects stale state."""
```

Contratos — la base que usarán después agentes, Council, Hermes, Research, Memory, GitHub, Deployment (todavía sin implementar aquí, solo el contrato):

```python
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
```

---

## B4 · state.py + state_machine.py (el DAG de estados válidos)

```python
from dataclasses import dataclass, replace
from typing import Mapping

from .contracts import NodeRuntime, WorkflowDefinition
from .enums import NodeStatus, WorkflowStatus


@dataclass(frozen=True)
class WorkflowState:
    definition: WorkflowDefinition
    status: WorkflowStatus = WorkflowStatus.CREATED
    version: int = 0
    sequence: int = 0
    nodes: Mapping[str, NodeRuntime] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.nodes is None:
            object.__setattr__(
                self,
                "nodes",
                {
                    node.node_id: NodeRuntime(node_id=node.node_id)
                    for node in self.definition.nodes
                },
            )

    def with_status(self, status: WorkflowStatus) -> "WorkflowState":
        return replace(self, status=status, version=self.version + 1)

    def with_node(self, runtime: NodeRuntime) -> "WorkflowState":
        updated = dict(self.nodes)
        updated[runtime.node_id] = runtime
        return replace(self, nodes=updated, version=self.version + 1)

    def next_sequence(self) -> "WorkflowState":
        return replace(self, sequence=self.sequence + 1)

    def node(self, node_id: str) -> NodeRuntime:
        return self.nodes[node_id]

    def all_nodes_passed(self) -> bool:
        return all(
            node.status == NodeStatus.PASSED
            for node in self.nodes.values()
        )
```

El corazón determinista de esta salida — no ejecuta agentes, no hace HTTP, no toca GitHub, no consulta un LLM. Solo determina si una transición es válida:

```python
from dataclasses import replace

from .enums import NodeStatus, WorkflowStatus
from .errors import InvalidTransitionError
from .state import WorkflowState


class WorkflowStateMachine:

    _workflow_transitions: dict[WorkflowStatus, set[WorkflowStatus]] = {
        WorkflowStatus.CREATED: {WorkflowStatus.READY, WorkflowStatus.CANCELLED},
        WorkflowStatus.READY: {WorkflowStatus.RUNNING, WorkflowStatus.CANCELLED},
        WorkflowStatus.RUNNING: {
            WorkflowStatus.WAITING, WorkflowStatus.PAUSED,
            WorkflowStatus.RECOVERING, WorkflowStatus.COMPLETED,
            WorkflowStatus.FAILED, WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.WAITING: {
            WorkflowStatus.RUNNING, WorkflowStatus.PAUSED,
            WorkflowStatus.RECOVERING, WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.PAUSED: {
            WorkflowStatus.RUNNING, WorkflowStatus.RECOVERING,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.RECOVERING: {
            WorkflowStatus.RUNNING, WorkflowStatus.WAITING,
            WorkflowStatus.FAILED, WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.COMPLETED: set(),
        WorkflowStatus.FAILED: {WorkflowStatus.RECOVERING, WorkflowStatus.CANCELLED},
        WorkflowStatus.CANCELLED: set(),
    }

    _node_transitions: dict[NodeStatus, set[NodeStatus]] = {
        NodeStatus.PENDING: {NodeStatus.READY, NodeStatus.BLOCKED, NodeStatus.SKIPPED},
        NodeStatus.READY: {NodeStatus.RUNNING, NodeStatus.BLOCKED, NodeStatus.SKIPPED},
        NodeStatus.RUNNING: {NodeStatus.WAITING, NodeStatus.PASSED, NodeStatus.FAILED},
        NodeStatus.WAITING: {NodeStatus.READY, NodeStatus.RUNNING, NodeStatus.FAILED},
        NodeStatus.PASSED: set(),
        NodeStatus.FAILED: {NodeStatus.READY, NodeStatus.RUNNING},
        NodeStatus.BLOCKED: {NodeStatus.READY, NodeStatus.SKIPPED},
        NodeStatus.SKIPPED: set(),
    }

    def transition_workflow(self, state: WorkflowState, target: WorkflowStatus) -> WorkflowState:
        allowed = self._workflow_transitions[state.status]
        if target not in allowed:
            raise InvalidTransitionError(
                f"Invalid workflow transition: {state.status.value} -> {target.value}"
            )
        return replace(state, status=target, version=state.version + 1)

    def transition_node(self, state: WorkflowState, node_id: str, target: NodeStatus) -> WorkflowState:
        runtime = state.node(node_id)
        allowed = self._node_transitions[runtime.status]
        if target not in allowed:
            raise InvalidTransitionError(
                f"Invalid node transition: {runtime.status.value} -> {target.value}"
            )
        updated = replace(runtime, status=target)
        return state.with_node(updated)
```

---

*Siguiente: Documento 3/4 — B5 (N/A, los Loops llegan en G6) + B6 (tests).*
