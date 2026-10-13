from workflow_core import (
    Goal,
    NodeDefinition,
    NodeStatus,
    WorkflowDefinition,
    WorkflowState,
    WorkflowStateMachine,
    WorkflowStatus,
)


def make_state() -> WorkflowState:
    definition = WorkflowDefinition(
        workflow_id="wf-001",
        name="test workflow",
        group="backend",
        goals=(
            Goal(
                goal_id="goal-001",
                description="Build backend",
            ),
        ),
        nodes=(
            NodeDefinition(
                node_id="node-001",
                name="Architecture",
                role="architecture",
            ),
            NodeDefinition(
                node_id="node-002",
                name="Execution",
                role="backend_primary_executor",
                dependencies=("node-001",),
            ),
        ),
    )

    return WorkflowState(definition=definition)


def test_workflow_transition() -> None:
    machine = WorkflowStateMachine()
    state = make_state()

    state = machine.transition_workflow(state, WorkflowStatus.READY)

    assert state.status == WorkflowStatus.READY


def test_node_transition() -> None:
    machine = WorkflowStateMachine()
    state = make_state()

    state = machine.transition_node(state, "node-001", NodeStatus.READY)

    assert state.node("node-001").status == NodeStatus.READY


def test_invalid_transition_is_rejected() -> None:
    machine = WorkflowStateMachine()
    state = make_state()

    state = machine.transition_workflow(state, WorkflowStatus.READY)
    state = machine.transition_workflow(state, WorkflowStatus.RUNNING)

    assert state.status == WorkflowStatus.RUNNING
