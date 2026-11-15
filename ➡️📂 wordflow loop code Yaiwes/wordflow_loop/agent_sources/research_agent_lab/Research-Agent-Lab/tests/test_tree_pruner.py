from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from agents.tree_pruner import PRUNEABLE_STATUSES, TreePrunerAgent
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState
from schemas.topic_pack import TopicPack


def _make_topic() -> TopicPack:
    return TopicPack(topic_name="test")


def _make_context(tmp_path: str) -> AgentContext:
    return AgentContext(
        artifact_store=ArtifactStore(Path(tmp_path)),
        memory_store=None,  # type: ignore
        tool_registry=None,  # type: ignore
        settings={},
    )


def _make_tree(
    nodes: list[dict],
    max_depth: int = 2,
    branch_id: str = "branch_1",
    root_id: str = "root",
) -> dict:
    return {
        "branch_id": branch_id,
        "root_id": root_id,
        "nodes": list(nodes),
        "status": "active",
        "max_depth": max_depth,
        "max_active_nodes": 3,
    }


LEAF_DEPTH_2_RESULT = {
    "node_id": "leaf_result",
    "parent_id": "parent",
    "depth": 2,
    "status": "max_depth_reached",
    "result": {"status": "passed"},
    "children_ids": [],
    "hypothesis": "leaf with result",
    "experiment_id": "exp_1",
    "patch_scope": "config change",
    "decision": {},
}

LEAF_DEPTH_2_NO_RESULT = {
    "node_id": "leaf_no_result",
    "parent_id": "parent",
    "depth": 2,
    "status": "max_depth_reached",
    "result": {},
    "children_ids": [],
    "hypothesis": "leaf without result",
    "experiment_id": "",
    "patch_scope": "config change",
    "decision": {},
}

SMOKE_PASSED_NODE = {
    "node_id": "smoke_passed",
    "parent_id": "root",
    "depth": 1,
    "status": "smoke_passed",
    "result": {"status": "passed", "metrics": {"ade": 0.30}},
    "children_ids": [],
    "hypothesis": "smoke passed",
    "experiment_id": "exp_smoke",
    "patch_scope": "config change",
    "decision": {},
}

SELECTED_NODE = {
    "node_id": "selected_node",
    "parent_id": "root",
    "depth": 1,
    "status": "selected",
    "result": {},
    "children_ids": [],
    "hypothesis": "selected node",
    "experiment_id": "",
    "patch_scope": "config change",
    "decision": {},
}


class TreePrunerAgentTest(TestCase):
    """Tests for TreePrunerAgent."""

    def test_noop_when_no_tree(self) -> None:
        """No tree in state -> notes contain "no tree"."""
        state = ResearchState(topic=_make_topic())
        with TemporaryDirectory() as tmp:
            result = TreePrunerAgent().run(state, _make_context(tmp))
        self.assertIn("no tree", result.notes[0])

    def test_prunes_max_depth_reached_without_result(self) -> None:
        """Node at max_depth with pruneable status and no result is pruned;
        smoke_passed sibling is kept."""
        tree = _make_tree(
            [
                {
                    "node_id": "root",
                    "parent_id": "",
                    "depth": 0,
                    "status": "active",
                    "result": {},
                    "children_ids": ["prune_me", "smoke_passed"],
                    "hypothesis": "root",
                    "experiment_id": "",
                    "patch_scope": "",
                    "decision": {},
                },
                {
                    "node_id": "prune_me",
                    "parent_id": "root",
                    "depth": 2,
                    "status": "max_depth_reached",
                    "result": {},
                    "children_ids": [],
                    "hypothesis": "prune this",
                    "experiment_id": "",
                    "patch_scope": "",
                    "decision": {},
                },
                SMOKE_PASSED_NODE,
            ],
            max_depth=2,
        )
        state = ResearchState(topic=_make_topic())
        state.values["experiment_tree"] = tree
        with TemporaryDirectory() as tmp:
            result = TreePrunerAgent().run(state, _make_context(tmp))
        updated = state.values["experiment_tree"]
        self.assertEqual(len(updated["nodes"]), 2)
        remaining_ids = {n["node_id"] for n in updated["nodes"]}
        self.assertNotIn("prune_me", remaining_ids)
        self.assertIn("smoke_passed", remaining_ids)

    def test_prunes_blocked_max_active_without_result(self) -> None:
        """Node at depth 2, max_depth=2, status=blocked_max_active, no result
        -> pruned."""
        tree = _make_tree(
            [
                {
                    "node_id": "root",
                    "parent_id": "",
                    "depth": 0,
                    "status": "active",
                    "result": {},
                    "children_ids": ["blocked_child"],
                    "hypothesis": "root",
                    "experiment_id": "",
                    "patch_scope": "",
                    "decision": {},
                },
                {
                    "node_id": "blocked_child",
                    "parent_id": "root",
                    "depth": 2,
                    "status": "blocked_max_active",
                    "result": {},
                    "children_ids": [],
                    "hypothesis": "blocked child",
                    "experiment_id": "",
                    "patch_scope": "",
                    "decision": {},
                },
            ],
            max_depth=2,
        )
        state = ResearchState(topic=_make_topic())
        state.values["experiment_tree"] = tree
        with TemporaryDirectory() as tmp:
            result = TreePrunerAgent().run(state, _make_context(tmp))
        updated = state.values["experiment_tree"]
        self.assertEqual(len(updated["nodes"]), 1)
        self.assertEqual(updated["nodes"][0]["node_id"], "root")

    def test_recursive_prune_parent_without_result(self) -> None:
        """Leaf pruned; parent (branched, no result, all children pruned) also
        pruned.  Root children_ids updated."""
        tree = _make_tree(
            [
                {
                    "node_id": "root",
                    "parent_id": "",
                    "depth": 0,
                    "status": "active",
                    "result": {},
                    "children_ids": ["parent"],
                    "hypothesis": "root",
                    "experiment_id": "",
                    "patch_scope": "",
                    "decision": {},
                },
                {
                    "node_id": "parent",
                    "parent_id": "root",
                    "depth": 1,
                    "status": "branched",
                    "result": {},
                    "children_ids": ["leaf1", "leaf2"],
                    "hypothesis": "parent",
                    "experiment_id": "",
                    "patch_scope": "",
                    "decision": {},
                },
                {
                    "node_id": "leaf1",
                    "parent_id": "parent",
                    "depth": 2,
                    "status": "pending",
                    "result": {},
                    "children_ids": [],
                    "hypothesis": "leaf 1",
                    "experiment_id": "",
                    "patch_scope": "",
                    "decision": {},
                },
                {
                    "node_id": "leaf2",
                    "parent_id": "parent",
                    "depth": 2,
                    "status": "max_depth_reached",
                    "result": {},
                    "children_ids": [],
                    "hypothesis": "leaf 2",
                    "experiment_id": "",
                    "patch_scope": "",
                    "decision": {},
                },
            ],
            max_depth=2,
        )
        state = ResearchState(topic=_make_topic())
        state.values["experiment_tree"] = tree
        with TemporaryDirectory() as tmp:
            result = TreePrunerAgent().run(state, _make_context(tmp))
        updated = state.values["experiment_tree"]
        # root should be the only surviving node
        self.assertEqual(len(updated["nodes"]), 1)
        self.assertEqual(updated["nodes"][0]["node_id"], "root")
        # root's children_ids should have the pruned parent removed
        self.assertEqual(updated["nodes"][0]["children_ids"], [])

    def test_does_not_prune_smoke_passed(self) -> None:
        """smoke_passed node with result is kept."""
        tree = _make_tree(
            [
                {
                    "node_id": "root",
                    "parent_id": "",
                    "depth": 0,
                    "status": "active",
                    "result": {},
                    "children_ids": ["smoke"],
                    "hypothesis": "root",
                    "experiment_id": "",
                    "patch_scope": "",
                    "decision": {},
                },
                SMOKE_PASSED_NODE,
            ],
            max_depth=2,
        )
        state = ResearchState(topic=_make_topic())
        state.values["experiment_tree"] = tree
        with TemporaryDirectory() as tmp:
            result = TreePrunerAgent().run(state, _make_context(tmp))
        updated = state.values["experiment_tree"]
        self.assertEqual(len(updated["nodes"]), 2)
        remaining_ids = {n["node_id"] for n in updated["nodes"]}
        self.assertIn("smoke_passed", remaining_ids)

    def test_does_not_prune_selected_node(self) -> None:
        """selected node is kept even if at max_depth."""
        tree = _make_tree(
            [
                {
                    "node_id": "root",
                    "parent_id": "",
                    "depth": 0,
                    "status": "active",
                    "result": {},
                    "children_ids": ["selected", "pending_dead"],
                    "hypothesis": "root",
                    "experiment_id": "",
                    "patch_scope": "",
                    "decision": {},
                },
                SELECTED_NODE,
                {
                    "node_id": "pending_dead",
                    "parent_id": "root",
                    "depth": 2,
                    "status": "pending",
                    "result": {},
                    "children_ids": [],
                    "hypothesis": "pending dead",
                    "experiment_id": "",
                    "patch_scope": "",
                    "decision": {},
                },
            ],
            max_depth=2,
        )
        state = ResearchState(topic=_make_topic())
        state.values["experiment_tree"] = tree
        with TemporaryDirectory() as tmp:
            result = TreePrunerAgent().run(state, _make_context(tmp))
        updated = state.values["experiment_tree"]
        self.assertEqual(len(updated["nodes"]), 2)
        remaining_ids = {n["node_id"] for n in updated["nodes"]}
        self.assertIn("selected_node", remaining_ids)
        self.assertNotIn("pending_dead", remaining_ids)

    def test_prunes_pending_at_or_beyond_max_depth(self) -> None:
        """pending node at depth >= max_depth is pruned."""
        tree = _make_tree(
            [
                {
                    "node_id": "root",
                    "parent_id": "",
                    "depth": 0,
                    "status": "active",
                    "result": {},
                    "children_ids": ["deep_pending"],
                    "hypothesis": "root",
                    "experiment_id": "",
                    "patch_scope": "",
                    "decision": {},
                },
                {
                    "node_id": "deep_pending",
                    "parent_id": "root",
                    "depth": 2,
                    "status": "pending",
                    "result": {},
                    "children_ids": [],
                    "hypothesis": "deep pending",
                    "experiment_id": "",
                    "patch_scope": "",
                    "decision": {},
                },
            ],
            max_depth=2,
        )
        state = ResearchState(topic=_make_topic())
        state.values["experiment_tree"] = tree
        with TemporaryDirectory() as tmp:
            result = TreePrunerAgent().run(state, _make_context(tmp))
        updated = state.values["experiment_tree"]
        self.assertEqual(len(updated["nodes"]), 1)
        self.assertEqual(updated["nodes"][0]["node_id"], "root")

    def test_reports_prune_count(self) -> None:
        """Notes contain the correct number of pruned nodes."""
        tree = _make_tree(
            [
                {
                    "node_id": "root",
                    "parent_id": "",
                    "depth": 0,
                    "status": "active",
                    "result": {},
                    "children_ids": ["dead1", "dead2"],
                    "hypothesis": "root",
                    "experiment_id": "",
                    "patch_scope": "",
                    "decision": {},
                },
                {
                    "node_id": "dead1",
                    "parent_id": "root",
                    "depth": 2,
                    "status": "pending",
                    "result": {},
                    "children_ids": [],
                    "hypothesis": "dead 1",
                    "experiment_id": "",
                    "patch_scope": "",
                    "decision": {},
                },
                {
                    "node_id": "dead2",
                    "parent_id": "root",
                    "depth": 2,
                    "status": "max_depth_reached",
                    "result": {},
                    "children_ids": [],
                    "hypothesis": "dead 2",
                    "experiment_id": "",
                    "patch_scope": "",
                    "decision": {},
                },
            ],
            max_depth=2,
        )
        state = ResearchState(topic=_make_topic())
        state.values["experiment_tree"] = tree
        with TemporaryDirectory() as tmp:
            result = TreePrunerAgent().run(state, _make_context(tmp))
        self.assertIn("pruned 2 node(s)", result.notes[0])

    def test_never_prunes_root_node(self) -> None:
        """Root node is protected even when all its children are pruned."""
        tree = _make_tree(
            [
                {
                    "node_id": "root",
                    "parent_id": "",
                    "depth": 0,
                    "status": "branched",
                    "result": {},
                    "children_ids": ["dead_only_child"],
                    "hypothesis": "root",
                    "experiment_id": "",
                    "patch_scope": "",
                    "decision": {},
                },
                {
                    "node_id": "dead_only_child",
                    "parent_id": "root",
                    "depth": 2,
                    "status": "pending",
                    "result": {},
                    "children_ids": [],
                    "hypothesis": "dead child",
                    "experiment_id": "",
                    "patch_scope": "",
                    "decision": {},
                },
            ],
            max_depth=2,
            root_id="root",
        )
        state = ResearchState(topic=_make_topic())
        state.values["experiment_tree"] = tree
        with TemporaryDirectory() as tmp:
            result = TreePrunerAgent().run(state, _make_context(tmp))
        updated = state.values["experiment_tree"]
        # Root must survive
        root_ids = [n["node_id"] for n in updated["nodes"]]
        self.assertIn("root", root_ids)
        # root_id in tree metadata must still be valid
        self.assertEqual(updated["root_id"], "root")
        # Dead child is pruned
        self.assertNotIn("dead_only_child", root_ids)


if __name__ == "__main__":
    main()
