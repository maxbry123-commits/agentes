from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from agents.branch_selection_agent import BranchSelectionAgent
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState
from memory.literature_memory import LiteratureMemoryStore
from schemas.topic_pack import TopicPack


def _make_topic(name: str = "test_topic") -> TopicPack:
    return TopicPack(
        topic_name=name,
        codebase={
            "repo_path": "/fake",
            "allowed_auto_edit": ["models/*", "trainer/*", "data/*", "cfg/virat/*"],
        },
    )


def _make_context(tmp_path: str) -> AgentContext:
    return AgentContext(
        artifact_store=ArtifactStore(Path(tmp_path)),
        memory_store=None,  # type: ignore
        tool_registry=None,  # type: ignore
        settings={},
    )


def _make_tree(**kwargs) -> dict:
    tree = {
        "branch_id": "branch_test",
        "root_id": "root_1",
        "status": "active",
        "max_depth": 2,
        "max_active_nodes": 3,
        "nodes": [],
    }
    tree.update(kwargs)
    return tree


class BranchSelectionAgentTest(TestCase):
    def test_selects_pending_node(self):
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            state.values["experiment_tree"] = _make_tree(
                nodes=[
                    {
                        "node_id": "root_1", "experiment_id": "e1",
                        "parent_id": "", "hypothesis": "Root H",
                        "patch_scope": "models/*", "result": {},
                        "decision": {}, "children_ids": ["child_1"],
                        "status": "active", "depth": 0,
                    },
                    {
                        "node_id": "child_1", "experiment_id": "e2",
                        "parent_id": "root_1", "hypothesis": "Child H",
                        "patch_scope": "data loader", "result": {},
                        "decision": {}, "children_ids": [],
                        "status": "pending", "depth": 1,
                    },
                ],
            )
            agent = BranchSelectionAgent()
            result = agent.run(state, _make_context(tmp))

            self.assertIn("selected branch node", result.notes[0])
            selected = state.values["selected_branch_node"]
            self.assertIsNotNone(selected)
            self.assertEqual(selected["node_id"], "child_1")
            self.assertEqual(selected["status"], "selected")

    def test_no_pending_returns_empty(self):
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            state.values["experiment_tree"] = _make_tree(
                nodes=[
                    {
                        "node_id": "root_1", "experiment_id": "e1",
                        "parent_id": "", "hypothesis": "H",
                        "patch_scope": "", "result": {},
                        "decision": {}, "children_ids": [],
                        "status": "active", "depth": 0,
                    },
                ],
            )
            agent = BranchSelectionAgent()
            result = agent.run(state, _make_context(tmp))

            self.assertIn("no pending branches", result.notes[0])
            self.assertNotIn("selected_branch_node", state.values)

    def test_prefers_lower_risk(self):
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            # Two pending nodes at same depth; "data loader" should score higher
            state.values["experiment_tree"] = _make_tree(
                nodes=[
                    {
                        "node_id": "root_1", "experiment_id": "e1",
                        "parent_id": "", "hypothesis": "Root",
                        "patch_scope": "", "result": {}, "decision": {},
                        "children_ids": ["child_data", "child_fusion"],
                        "status": "active", "depth": 0,
                    },
                    {
                        "node_id": "child_data", "experiment_id": "e2",
                        "parent_id": "root_1", "hypothesis": "Data H",
                        "patch_scope": "data loader modification",
                        "result": {}, "decision": {}, "children_ids": [],
                        "status": "pending", "depth": 1,
                    },
                    {
                        "node_id": "child_fusion", "experiment_id": "e3",
                        "parent_id": "root_1", "hypothesis": "Fusion H",
                        "patch_scope": "fusion layer change",
                        "result": {}, "decision": {}, "children_ids": [],
                        "status": "pending", "depth": 1,
                    },
                ],
            )
            agent = BranchSelectionAgent()
            agent.run(state, _make_context(tmp))

            selected = state.values["selected_branch_node"]
            # "data loader" gets +0.3 risk bonus vs "fusion" gets +0.1
            self.assertEqual(selected["node_id"], "child_data")

    def test_marks_selected(self):
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            state.values["experiment_tree"] = _make_tree(
                nodes=[
                    {
                        "node_id": "root_1", "experiment_id": "e1",
                        "parent_id": "", "hypothesis": "Root",
                        "patch_scope": "", "result": {}, "decision": {},
                        "children_ids": ["pending_1"],
                        "status": "active", "depth": 0,
                    },
                    {
                        "node_id": "pending_1", "experiment_id": "e2",
                        "parent_id": "root_1", "hypothesis": "Pending H",
                        "patch_scope": "config adjustment",
                        "result": {}, "decision": {}, "children_ids": [],
                        "status": "pending", "depth": 1,
                    },
                ],
            )
            agent = BranchSelectionAgent()
            agent.run(state, _make_context(tmp))

            tree = state.values["experiment_tree"]
            selected_in_tree = [
                n for n in tree["nodes"] if n["node_id"] == "pending_1"
            ][0]
            self.assertEqual(selected_in_tree["status"], "selected")

    def test_noop_when_no_tree(self):
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            agent = BranchSelectionAgent()
            result = agent.run(state, _make_context(tmp))
            self.assertIn("no experiment_tree", result.notes[0])

    def test_skips_nodes_at_max_depth(self):
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            state.values["experiment_tree"] = _make_tree(
                max_depth=2,
                nodes=[
                    {
                        "node_id": "deep_node", "experiment_id": "e1",
                        "parent_id": "", "hypothesis": "Too deep",
                        "patch_scope": "", "result": {}, "decision": {},
                        "children_ids": [],
                        "status": "pending", "depth": 2,
                    },
                ],
            )
            agent = BranchSelectionAgent()
            result = agent.run(state, _make_context(tmp))
            self.assertIn("no pending branches", result.notes[0])

    def test_prefers_lower_depth(self):
        """Shallower nodes should score higher when risk is equal."""
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            state.values["experiment_tree"] = _make_tree(
                nodes=[
                    {
                        "node_id": "root_1", "experiment_id": "e1",
                        "parent_id": "", "hypothesis": "Root",
                        "patch_scope": "", "result": {}, "decision": {},
                        "children_ids": ["shallow", "deep"],
                        "status": "active", "depth": 0,
                    },
                    {
                        "node_id": "shallow", "experiment_id": "e2",
                        "parent_id": "root_1", "hypothesis": "Depth 1",
                        "patch_scope": "config adjustment",
                        "result": {}, "decision": {}, "children_ids": [],
                        "status": "pending", "depth": 1,
                    },
                    {
                        "node_id": "deep", "experiment_id": "e3",
                        "parent_id": "root_1", "hypothesis": "Depth 2 same scope",
                        "patch_scope": "config adjustment",
                        "result": {}, "decision": {}, "children_ids": [],
                        "status": "pending", "depth": 2,
                    },
                ],
            )
            agent = BranchSelectionAgent()
            agent.run(state, _make_context(tmp))

            selected = state.values["selected_branch_node"]
            # Depth 1 should beat depth 2 when risk/scope are equal
            self.assertEqual(selected["node_id"], "shallow")

    def test_loads_tree_from_store_when_state_has_none(self):
        with TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            store = LiteratureMemoryStore(db_path)

            # Pre-populate the store with a pending tree
            branch = {
                "branch_id": "branch_from_db",
                "root_id": "root_db",
                "status": "active",
                "max_depth": 2,
                "max_active_nodes": 3,
                "nodes": [
                    {
                        "node_id": "root_db", "experiment_id": "e1",
                        "parent_id": "", "hypothesis": "Persisted root",
                        "patch_scope": "", "result": {}, "decision": {},
                        "children_ids": ["pend_db"],
                        "status": "active", "depth": 0,
                    },
                    {
                        "node_id": "pend_db", "experiment_id": "e2",
                        "parent_id": "root_db", "hypothesis": "Persisted pending",
                        "patch_scope": "data loader",
                        "result": {}, "decision": {}, "children_ids": [],
                        "status": "pending", "depth": 1,
                    },
                ],
            }
            store.write_branch(branch, "test_topic")

            topic = _make_topic()
            state = ResearchState(topic=topic)
            # state has no experiment_tree
            self.assertNotIn("experiment_tree", state.values)

            agent = BranchSelectionAgent(lit_memory_store=store)
            result = agent.run(state, _make_context(tmp))

            self.assertIn("selected branch node", result.notes[0])
            selected = state.values["selected_branch_node"]
            self.assertEqual(selected["node_id"], "pend_db")
            # Tree should now be in state
            self.assertIn("experiment_tree", state.values)


class MultiBranchSelectionTest(TestCase):
    """Tests for top-N selection with max_parallel_branches."""

    def test_selects_top2_pending_nodes(self):
        """With max_parallel_branches=2, selects the 2 highest-scored nodes."""
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            tree = {
                "branch_id": "mb", "root_id": "r",
                "status": "active", "max_depth": 2, "max_active_nodes": 3,
                "nodes": [
                    {"node_id": "r", "parent_id": "", "hypothesis": "R",
                     "children_ids": ["p1", "p2", "p3"], "status": "active",
                     "result": {}, "decision": {}, "depth": 0},
                    {"node_id": "p1", "parent_id": "r",
                     "hypothesis": "Data loader tweak", "patch_scope": "data loader",
                     "children_ids": [], "status": "pending",
                     "result": {}, "decision": {}, "depth": 1},
                    {"node_id": "p2", "parent_id": "r",
                     "hypothesis": "Config change", "patch_scope": "config",
                     "children_ids": [], "status": "pending",
                     "result": {}, "decision": {}, "depth": 1},
                    {"node_id": "p3", "parent_id": "r",
                     "hypothesis": "Fusion layer", "patch_scope": "fusion",
                     "children_ids": [], "status": "pending",
                     "result": {}, "decision": {}, "depth": 1},
                ],
            }
            state.values["experiment_tree"] = tree
            ctx = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None, tool_registry=None,
                settings={"max_parallel_branches": 2},
            )
            agent = BranchSelectionAgent()
            result = agent.run(state, ctx)

            selected_nodes = state.values.get("selected_branch_nodes", [])
            self.assertEqual(len(selected_nodes), 2)
            # data loader (score 0.5) > config (score -0.1) > fusion (score -0.2)
            ids = [n["node_id"] for n in selected_nodes]
            self.assertIn("p1", ids)
            # Both should be marked selected
            self.assertEqual(selected_nodes[0]["status"], "selected")
            self.assertEqual(selected_nodes[1]["status"], "selected")
            # Backward compat: selected_branch_node is first
            self.assertEqual(state.values["selected_branch_node"]["node_id"], ids[0])

    def test_only_one_pending_selects_one(self):
        """With only 1 pending node but max_parallel=2, selects just 1."""
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            tree = {
                "branch_id": "mb2", "root_id": "r2",
                "status": "active", "max_depth": 2, "max_active_nodes": 3,
                "nodes": [
                    {"node_id": "r2", "parent_id": "", "hypothesis": "R",
                     "children_ids": ["only"], "status": "active",
                     "result": {}, "decision": {}, "depth": 0},
                    {"node_id": "only", "parent_id": "r2",
                     "hypothesis": "Only one", "patch_scope": "config",
                     "children_ids": [], "status": "pending",
                     "result": {}, "decision": {}, "depth": 1},
                ],
            }
            state.values["experiment_tree"] = tree
            ctx = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None, tool_registry=None,
                settings={"max_parallel_branches": 2},
            )
            agent = BranchSelectionAgent()
            result = agent.run(state, ctx)
            selected_nodes = state.values.get("selected_branch_nodes", [])
            self.assertEqual(len(selected_nodes), 1)

    def test_default_max_parallel_is_one(self):
        """Without max_parallel_branches setting, selects only 1 node (backward compat)."""
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            tree = {
                "branch_id": "mb3", "root_id": "r3",
                "status": "active", "max_depth": 2, "max_active_nodes": 3,
                "nodes": [
                    {"node_id": "r3", "parent_id": "", "hypothesis": "R",
                     "children_ids": ["a", "b"], "status": "active",
                     "result": {}, "decision": {}, "depth": 0},
                    {"node_id": "a", "parent_id": "r3",
                     "hypothesis": "A", "patch_scope": "config",
                     "children_ids": [], "status": "pending",
                     "result": {}, "decision": {}, "depth": 1},
                    {"node_id": "b", "parent_id": "r3",
                     "hypothesis": "B", "patch_scope": "data loader",
                     "children_ids": [], "status": "pending",
                     "result": {}, "decision": {}, "depth": 1},
                ],
            }
            state.values["experiment_tree"] = tree
            ctx = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None, tool_registry=None,
                settings={},  # no max_parallel_branches
            )
            agent = BranchSelectionAgent()
            result = agent.run(state, ctx)
            selected_nodes = state.values.get("selected_branch_nodes", [])
            self.assertEqual(len(selected_nodes), 1)


if __name__ == "__main__":
    main()
