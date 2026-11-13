import json
import unittest
from pathlib import Path

from runtime.src.core.graph_visual_projection import (
    VisualEdge,
    VisualNode,
    VisualProjectionError,
    build_crazy_wall_projection,
    build_visual_projection,
)


ROOT = Path(__file__).parents[2]


class GraphVisualProjectionG026Tests(unittest.TestCase):
    def test_projection_is_stable_and_renderer_agnostic(self):
        nodes = [
            VisualNode("B", "Build", "task", "RUNNING", "opencode", 5, "code"),
            VisualNode("A", "Audit", "task", "DONE", "claude_code", 9, "audit"),
        ]
        edges = [VisualEdge("A", "B", "depends_on")]
        first = build_visual_projection(nodes, edges)
        second = build_visual_projection(reversed(nodes), reversed(edges))
        self.assertEqual(first, second)
        self.assertEqual(first["nodes"][0]["id"], "A")
        contract = first["renderer_contract"]
        self.assertEqual(contract["enrichment_preference"], "graphify")
        self.assertFalse(contract["graphify_runtime_verified"])
        self.assertFalse(contract["graphology_required"])
        self.assertFalse(contract["sigma_required"])
        self.assertEqual(len(first["sha256"]), 64)

    def test_missing_edge_endpoint_fails_closed(self):
        with self.assertRaisesRegex(VisualProjectionError, "EDGE_ENDPOINT_MISSING"):
            build_visual_projection(
                [VisualNode("A", "A", "task", "DONE")],
                [VisualEdge("A", "B", "depends_on")],
            )

    def test_duplicate_node_id_fails_closed(self):
        with self.assertRaisesRegex(VisualProjectionError, "DUPLICATE_NODE_ID"):
            build_visual_projection(
                [VisualNode("A", "A", "task", "DONE"), VisualNode("A", "A2", "task", "DONE")],
                [],
            )

    def test_real_crazy_wall_projects_all_required_panels(self):
        task_nodes = json.loads(
            (ROOT / "Crazy Wall Orquestador" / "TASK-NODES.json").read_text(encoding="utf-8")
        )
        checkpoint = json.loads(
            (ROOT / "Crazy Wall Orquestador" / "CHECKPOINT.json").read_text(encoding="utf-8")
        )
        projection = build_crazy_wall_projection(task_nodes, checkpoint)
        types = {node["type"] for node in projection["nodes"]}
        self.assertTrue({"task", "gap", "agent", "evidence", "checkpoint"}.issubset(types))
        self.assertEqual(projection["panels"]["tasks"], len(task_nodes["nodes"]))
        self.assertEqual(projection["panels"]["queue"], len(projection["queue"]))
        self.assertGreater(projection["panels"]["agents"], 0)
        self.assertGreater(projection["panels"]["evidence"], 0)
        self.assertEqual(projection["panels"]["checkpoints"], 1)

    def test_invalid_source_documents_fail_closed(self):
        checkpoint = {"checkpoint_id": "cp", "status": "ACTIVE"}
        with self.assertRaisesRegex(VisualProjectionError, "TASK_NODES_SCHEMA_INVALID"):
            build_crazy_wall_projection({"schema": "wrong", "nodes": [{}]}, checkpoint)
        with self.assertRaisesRegex(VisualProjectionError, "CHECKPOINT_ID_REQUIRED"):
            build_crazy_wall_projection(
                {"schema": "yaiwes.crazywall-dag/v1", "nodes": [{"id": "A"}]}, {}
            )


if __name__ == "__main__":
    unittest.main()
