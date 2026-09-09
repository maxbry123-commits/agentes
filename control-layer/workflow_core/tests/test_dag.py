from workflow_core.contracts import NodeDefinition
from workflow_core.dag import DAGDefinition
from workflow_core.dag_validator import DAGValidator
from workflow_core.errors import ContractViolationError
import pytest


def test_valid_dag() -> None:
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

    DAGValidator().validate(dag)


def test_cycle_is_rejected() -> None:
    dag = DAGDefinition(
        dag_id="dag-cycle",
        workflow_id="wf-001",
        version=1,
        nodes=(
            NodeDefinition(
                node_id="a", name="A", role="architecture",
                dependencies=("b",),
            ),
            NodeDefinition(
                node_id="b", name="B",
                role="backend_primary_executor",
                dependencies=("a",),
            ),
        ),
    )

    with pytest.raises(ContractViolationError):
        DAGValidator().validate(dag)
