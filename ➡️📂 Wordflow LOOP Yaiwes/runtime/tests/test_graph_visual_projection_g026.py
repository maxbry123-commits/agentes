import pytest

from runtime.src.core.graph_visual_projection import (
    VisualEdge,
    VisualNode,
    VisualProjectionError,
    build_visual_projection,
)


def test_projection_is_stable_and_renderer_agnostic():
    nodes = [
        VisualNode("B", "Build", "task", "RUNNING", "opencode", 5, "code"),
        VisualNode("A", "Audit", "task", "DONE", "claude_code", 9, "audit"),
    ]
    edges = [VisualEdge("A", "B", "depends_on")]
    first = build_visual_projection(nodes, edges)
    second = build_visual_projection(reversed(nodes), reversed(edges))
    assert first == second
    assert first["nodes"][0]["id"] == "A"
    assert first["renderer_contract"]["preferred"] == "graphology+sigma"
    assert first["renderer_contract"]["core_dependency"] is False
    assert len(first["sha256"]) == 64


def test_missing_edge_endpoint_fails_closed():
    with pytest.raises(VisualProjectionError, match="EDGE_ENDPOINT_MISSING"):
        build_visual_projection(
            [VisualNode("A", "A", "task", "DONE")],
            [VisualEdge("A", "B", "depends_on")],
        )


def test_duplicate_node_id_fails_closed():
    with pytest.raises(VisualProjectionError, match="DUPLICATE_NODE_ID"):
        build_visual_projection(
            [
                VisualNode("A", "A", "task", "DONE"),
                VisualNode("A", "A2", "task", "DONE"),
            ],
            [],
        )
