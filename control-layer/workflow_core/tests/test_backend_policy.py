from workflow_core.contracts import NodeDefinition
from workflow_core.dag import DAGDefinition
from workflow_core.sheriff import DeterministicSheriff

# Import local policy (path relative when running from control-layer)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config.policies.backend import backend_policy


def test_backend_policy_approves() -> None:
    dag = DAGDefinition(
        dag_id="d1",
        workflow_id="wf1",
        version=1,
        nodes=(
            NodeDefinition(node_id="a", name="Arch", role="architecture"),
            NodeDefinition(
                node_id="b",
                name="Exec",
                role="backend_primary_executor",
                dependencies=("a",),
            ),
        ),
    )
    decision = DeterministicSheriff(backend_policy).inspect(dag, {"group": "backend"})
    assert decision.allowed is True


def test_backend_policy_rejects_unknown_role() -> None:
    dag = DAGDefinition(
        dag_id="d1",
        workflow_id="wf1",
        version=1,
        nodes=(
            NodeDefinition(node_id="a", name="X", role="unknown_role"),
        ),
    )
    decision = DeterministicSheriff(backend_policy).inspect(dag, {"group": "backend"})
    assert decision.allowed is False
