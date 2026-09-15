"""Tests for tools.tree_visualizer."""

from __future__ import annotations

from unittest import TestCase

from tools.tree_visualizer import export_mermaid, render_ascii_tree


def _make_sample_tree() -> dict:
    """Create the sample experiment tree used in the task description."""
    return {
        "branch_id": "branch_1",
        "root_id": "root_1",
        "status": "active",
        "max_depth": 2,
        "max_active_nodes": 3,
        "nodes": [
            {
                "node_id": "root_1",
                "experiment_id": "exp_root",
                "parent_id": "",
                "hypothesis": "Root hypothesis",
                "patch_scope": "",
                "result": {},
                "decision": {},
                "children_ids": ["pend_a", "pend_b"],
                "status": "active",
                "depth": 0,
            },
            {
                "node_id": "pend_a",
                "experiment_id": "exp_a",
                "parent_id": "root_1",
                "hypothesis": "Data loader tweak may improve ADE",
                "patch_scope": "data loader",
                "result": {
                    "status": "passed",
                    "metrics": {"ade": 0.27, "fde": 0.15},
                },
                "decision": {"action": "continue"},
                "children_ids": [],
                "status": "smoke_passed",
                "depth": 1,
            },
            {
                "node_id": "pend_b",
                "experiment_id": "exp_b",
                "parent_id": "root_1",
                "hypothesis": "Fusion layer simplification",
                "patch_scope": "fusion layer",
                "result": {},
                "decision": {},
                "children_ids": [],
                "status": "pending",
                "depth": 1,
            },
        ],
    }


class TestRenderAsciiTree(TestCase):
    """Tests for render_ascii_tree."""

    def test_render_ascii_tree_contains_root(self):
        """Output contains root node_id and status."""
        tree = _make_sample_tree()
        output = render_ascii_tree(tree)
        self.assertIn("root_1", output)
        self.assertIn("[active]", output)

    def test_render_ascii_tree_contains_children(self):
        """Output contains child node_ids and statuses."""
        tree = _make_sample_tree()
        output = render_ascii_tree(tree)
        self.assertIn("pend_a", output)
        self.assertIn("[smoke_passed]", output)
        self.assertIn("pend_b", output)
        self.assertIn("[pending]", output)

    def test_render_ascii_tree_shows_metrics(self):
        """Output contains hypothesis text 'ADE' and metric values."""
        tree = _make_sample_tree()
        output = render_ascii_tree(tree)
        self.assertIn("ADE", output)
        self.assertIn("0.27", output)
        self.assertIn("0.15", output)

    def test_render_ascii_tree_empty_nodes(self):
        """Empty nodes list returns '(empty tree)'."""
        tree = {"branch_id": "b1", "root_id": "", "nodes": []}
        output = render_ascii_tree(tree)
        self.assertEqual("(empty tree)", output)

    def test_render_ascii_tree_cycle_detection(self):
        """Cyclic tree (a -> b -> a) does not crash — visited guard."""
        tree = {
            "branch_id": "b1",
            "root_id": "root_1",
            "status": "active",
            "max_depth": 2,
            "max_active_nodes": 3,
            "nodes": [
                {
                    "node_id": "root_1", "experiment_id": "e1", "parent_id": "",
                    "hypothesis": "Root", "patch_scope": "", "result": {}, "decision": {},
                    "children_ids": ["child_a"], "status": "active", "depth": 0,
                },
                {
                    "node_id": "child_a", "experiment_id": "e2", "parent_id": "root_1",
                    "hypothesis": "Child A", "patch_scope": "data loader",
                    "result": {}, "decision": {},
                    "children_ids": ["root_1"],  # cycle back to root
                    "status": "pending", "depth": 1,
                },
            ],
        }
        output = render_ascii_tree(tree)
        self.assertIn("root_1", output)
        self.assertIn("child_a", output)
        self.assertIn("cycle", output.lower())


class TestExportMermaid(TestCase):
    """Tests for export_mermaid."""

    def test_export_mermaid_contains_header(self):
        """Output starts with 'graph TD'."""
        tree = _make_sample_tree()
        output = export_mermaid(tree)
        self.assertTrue(output.startswith("graph TD"))

    def test_export_mermaid_contains_nodes(self):
        """Output contains node_ids in labels."""
        tree = _make_sample_tree()
        output = export_mermaid(tree)
        self.assertIn("root_1", output)
        self.assertIn("pend_a", output)
        self.assertIn("pend_b", output)

    def test_export_mermaid_contains_edges(self):
        """Output contains '-->' edge markers."""
        tree = _make_sample_tree()
        output = export_mermaid(tree)
        self.assertIn("-->", output)

    def test_export_mermaid_status_shapes(self):
        """smoke_passed uses () rounded rect; pending uses {} diamond."""
        tree = _make_sample_tree()
        output = export_mermaid(tree)
        # smoke_passed node should use rounded rectangle ( )
        self.assertIn("(pend_a<br/>smoke_passed", output)
        # pending node should use diamond { }
        self.assertIn("{pend_b<br/>pending", output)

    def test_export_mermaid_cycle_detection(self):
        """Cyclic tree does not crash export_mermaid — visited guard."""
        tree = {
            "branch_id": "b1",
            "root_id": "root_1",
            "status": "active",
            "max_depth": 2,
            "max_active_nodes": 3,
            "nodes": [
                {
                    "node_id": "root_1", "experiment_id": "e1", "parent_id": "",
                    "hypothesis": "Root", "patch_scope": "", "result": {}, "decision": {},
                    "children_ids": ["child_a"], "status": "active", "depth": 0,
                },
                {
                    "node_id": "child_a", "experiment_id": "e2", "parent_id": "root_1",
                    "hypothesis": "Child A", "patch_scope": "data loader",
                    "result": {}, "decision": {},
                    "children_ids": ["root_1"],  # cycle back to root
                    "status": "pending", "depth": 1,
                },
            ],
        }
        output = export_mermaid(tree)
        self.assertIn("graph TD", output)
        self.assertIn("root_1", output)
        self.assertIn("child_a", output)
