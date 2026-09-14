from workflow_core.contracts import NodeDefinition
from workflow_core.dag import DAGDefinition
from workflow_core.policies import WorkflowPolicy
from workflow_core.sheriff import DeterministicSheriff


def test_gate_approve() -> None:
    policy = WorkflowPolicy(
        allowed_groups=frozenset({"backend"}),
        allowed_roles=frozenset({"architecture", "backend_primary_executor"}),
    )
    dag = DAGDefinition(
        dag_id="t1",
        workflow_id="wf1",
        version=1,
        nodes=(
            NodeDefinition(node_id="n1", name="Arch", role="architecture"),
            NodeDefinition(
                node_id="n2",
                name="Exec",
                role="backend_primary_executor",
                dependencies=("n1",),
            ),
        ),
    )
    decision = DeterministicSheriff(policy).inspect(dag, {"group": "backend"})
    assert decision.allowed is True
