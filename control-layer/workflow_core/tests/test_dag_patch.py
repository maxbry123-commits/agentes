from workflow_core.contracts import NodeDefinition
from workflow_core.dag import DAGDefinition
from workflow_core.dag_patch import DAGPatch, DAGPatchEngine
from workflow_core.errors import VersionConflictError
import pytest


def test_dag_patch_add_node() -> None:
    dag = DAGDefinition(
        dag_id="d1",
        workflow_id="wf1",
        version=1,
        nodes=(
            NodeDefinition(node_id="a", name="A", role="architecture"),
        ),
    )
    patch = DAGPatch(
        patch_id="p1",
        base_version=1,
        add_nodes=(
            NodeDefinition(
                node_id="b",
                name="B",
                role="backend_primary_executor",
                dependencies=("a",),
            ),
        ),
    )
    new_dag = DAGPatchEngine().apply(dag, patch)
    assert new_dag.version == 2
    assert len(new_dag.nodes) == 2


def test_dag_patch_version_conflict() -> None:
    dag = DAGDefinition(
        dag_id="d1",
        workflow_id="wf1",
        version=2,
        nodes=(
            NodeDefinition(node_id="a", name="A", role="architecture"),
        ),
    )
    patch = DAGPatch(patch_id="p1", base_version=1)
    with pytest.raises(VersionConflictError):
        DAGPatchEngine().apply(dag, patch)
