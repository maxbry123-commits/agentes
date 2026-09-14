import pytest

from core.code_graph_workspace import (
    CodeGraphEdge,
    CodeGraphError,
    CodeGraphNode,
    build_code_graph,
    graph_sha256,
    serialize_code_graph,
    task_dependency_manifest,
)


def _graph():
    return build_code_graph(
        [
            CodeGraphNode("src:a", "source_file", {"path": "a.py"}),
            CodeGraphNode("t:1", "task", {"source": "director"}),
            CodeGraphNode("t:2", "task", {"source": "generated"}),
            CodeGraphNode("ev:1", "evidence", {"ok": True}),
        ],
        [
            CodeGraphEdge("src:a", "t:1", "extracts"),
            CodeGraphEdge("t:2", "t:1", "depends_on"),
            CodeGraphEdge("t:2", "ev:1", "produces"),
        ],
    )


def test_serialization_is_deterministic():
    graph = _graph()
    assert serialize_code_graph(graph) == serialize_code_graph(graph)
    assert graph_sha256(graph) == graph_sha256(graph)


def test_projects_to_existing_dag_contract():
    manifest = task_dependency_manifest(_graph())
    assert manifest["nodes"]["t:2"]["depends_on"] == ["t:1"]


def test_missing_edge_endpoint_fails_closed():
    with pytest.raises(CodeGraphError):
        build_code_graph(
            [CodeGraphNode("t:1", "task", {})],
            [CodeGraphEdge("t:1", "missing", "depends_on")],
        )


def test_non_json_payload_fails_closed():
    with pytest.raises(CodeGraphError):
        build_code_graph([CodeGraphNode("t:1", "task", {"bad": {1, 2}})], [])


def test_dependency_edge_requires_tasks():
    graph = build_code_graph(
        [
            CodeGraphNode("src:a", "source_file", {}),
            CodeGraphNode("t:1", "task", {}),
        ],
        [CodeGraphEdge("src:a", "t:1", "depends_on")],
    )
    with pytest.raises(CodeGraphError):
        task_dependency_manifest(graph)
