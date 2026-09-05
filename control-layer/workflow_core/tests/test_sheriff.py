from workflow_core.contracts import NodeDefinition
from workflow_core.dag import DAGDefinition
from workflow_core.policies import WorkflowPolicy
from workflow_core.sheriff import DeterministicSheriff


def test_sheriff_approves_valid() -> None:
    policy = WorkflowPolicy(
        allowed_groups=frozenset({"backend"}),
        allowed_roles=frozenset({"architecture", "backend_primary_executor"}),
    )
    sheriff = DeterministicSheriff(policy)

    dag = DAGDefinition(
        dag_id="dag-001",
        workflow_id="wf-001",
        version=1,
        nodes=(
            NodeDefinition(node_id="a", name="A", role="architecture"),
            NodeDefinition(
                node_id="b", name="B",
                role="backend_primary_executor",
                dependencies=("a",),
            ),
        ),
    )

    decision = sheriff.inspect(dag, {"group": "backend"})
    assert decision.allowed is True


def test_sheriff_rejects_bad_role() -> None:
    policy = WorkflowPolicy(
        allowed_groups=frozenset({"backend"}),
        allowed_roles=frozenset({"architecture"}),
    )
    sheriff = DeterministicSheriff(policy)

    dag = DAGDefinition(
        dag_id="dag-001",
        workflow_id="wf-001",
        version=1,
        nodes=(
            NodeDefinition(node_id="a", name="A", role="unknown_role"),
        ),
    )

    decision = sheriff.inspect(dag, {"group": "backend"})
    assert decision.allowed is False
    assert len(decision.violations) > 0
