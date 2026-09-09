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
