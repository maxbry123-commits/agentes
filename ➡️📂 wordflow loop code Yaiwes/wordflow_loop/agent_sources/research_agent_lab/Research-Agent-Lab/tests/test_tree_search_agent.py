from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from agents.tree_search_agent import BranchToPlanAgent, TreeSearchAgent, _infer_files, _node_to_plan
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState
from schemas.experiment_plan import ExperimentPlan
from schemas.experiment_tree import ExperimentBranch, ExperimentNode
from schemas.topic_pack import TopicPack


def _make_topic() -> TopicPack:
    return TopicPack(
        topic_name="test_topic",
        experiment_metrics=["ADE", "FDE"],
        codebase={"repo_path": "/fake"},
    )


def _make_context(tmp_path: str) -> AgentContext:
    return AgentContext(
        artifact_store=ArtifactStore(Path(tmp_path)),
        memory_store=None,  # type: ignore
        tool_registry=None,  # type: ignore
        settings={},
    )


class ExperimentNodeSchemaTest(TestCase):
    def test_default_factory_ids(self):
        node = ExperimentNode()
        self.assertTrue(node.node_id.startswith("expnode_"))
        self.assertEqual(node.status, "pending")
        self.assertEqual(node.depth, 0)

    def test_children_ids_initialized_empty(self):
        node = ExperimentNode()
        self.assertEqual(node.children_ids, [])

    def test_branch_id_auto_generated(self):
        branch = ExperimentBranch()
        self.assertTrue(branch.branch_id.startswith("branch_"))
        self.assertEqual(branch.max_depth, 2)
        self.assertEqual(branch.max_active_nodes, 3)


class TreeSearchAgentTest(TestCase):
    def test_creates_root_node_from_state(self):
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            state.values["experiment_plans"] = [
                {"experiment_id": "exp1", "hypothesis": "Test H", "modification": "patch"}
            ]
            state.values["experiment_results"] = [
                {"result_id": "r1", "status": "passed", "metrics": {"ade": 0.3}}
            ]
            state.values["experiment_decision"] = {"action": "continue", "reason": "ok"}

            agent = TreeSearchAgent()
            agent.run(state, _make_context(tmp))

            tree = state.values["experiment_tree"]
            self.assertIsNotNone(tree)
            self.assertTrue(len(tree["nodes"]) >= 1)
            root = tree["nodes"][0]
            self.assertEqual(root["hypothesis"], "Test H")
            self.assertEqual(root["depth"], 0)

    def test_no_branching_when_decision_continue(self):
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            state.values["experiment_plans"] = [
                {"experiment_id": "exp1", "hypothesis": "H"}
            ]
            state.values["experiment_results"] = [
                {"result_id": "r1", "status": "passed"}
            ]
            state.values["experiment_decision"] = {"action": "continue"}

            agent = TreeSearchAgent()
            agent.run(state, _make_context(tmp))

            tree = state.values["experiment_tree"]
            self.assertEqual(len(tree["nodes"]), 1)

    def test_branches_when_decision_investigate_unparsed(self):
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            state.values["experiment_plans"] = [
                {"experiment_id": "exp1", "hypothesis": "H", "modification": "patch"}
            ]
            state.values["experiment_results"] = [
                {"result_id": "r1", "status": "unparsed"}
            ]
            state.values["experiment_decision"] = {
                "action": "investigate",
                "reason": "no metrics parsed",
            }

            agent = TreeSearchAgent()
            agent.run(state, _make_context(tmp))

            tree = state.values["experiment_tree"]
            self.assertGreaterEqual(len(tree["nodes"]), 2)
            root = [n for n in tree["nodes"] if n["depth"] == 0][0]
            children = [n for n in tree["nodes"] if n["depth"] == 1]
            self.assertGreaterEqual(len(children), 2)
            for child in children:
                self.assertEqual(child["parent_id"], root["node_id"])
                self.assertEqual(child["status"], "pending")

    def test_max_depth_enforced(self):
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            state.values["experiment_plans"] = [
                {"experiment_id": "exp1", "hypothesis": "H"}
            ]
            state.values["experiment_results"] = [
                {"result_id": "r1", "status": "failed"}
            ]
            state.values["experiment_decision"] = {
                "action": "rollback",
                "reason": "failed",
            }
            # Pre-populate tree: root + 3 pending nodes at depth 1
            from dataclasses import asdict
            from schemas.experiment_tree import ExperimentBranch, ExperimentNode as EN
            existing = ExperimentBranch()
            root = EN(node_id="r", experiment_id="e1", hypothesis="H", depth=0, status="active")
            children = [
                EN(node_id=f"c{i}", experiment_id=f"e{i+1}", parent_id="r",
                   hypothesis=f"H{i}", depth=1, status="pending")
                for i in range(3)
            ]
            existing.root_id = root.node_id
            existing.nodes = [root] + children
            state.values["experiment_tree"] = asdict(existing)

            agent = TreeSearchAgent()
            agent.run(state, _make_context(tmp))

            # Max active reached (3 pending) — no new branches created
            tree = state.values["experiment_tree"]
            self.assertEqual(len(tree["nodes"]), 4)

    def test_tree_artifact_persisted(self):
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            state.values["experiment_plans"] = [
                {"experiment_id": "exp1", "hypothesis": "H", "modification": "patch"}
            ]
            state.values["experiment_results"] = [
                {"result_id": "r1", "status": "unparsed"}
            ]
            state.values["experiment_decision"] = {"action": "investigate"}

            agent = TreeSearchAgent()
            agent.run(state, _make_context(tmp))

            # Check artifact saved
            files = list(Path(tmp).rglob("*.json"))
            tree_files = [
                f for f in files if "experiment_trees" in str(f)
            ]
            self.assertEqual(len(tree_files), 1)

    def test_no_branching_when_decision_hold(self):
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            state.values["experiment_plans"] = [{"experiment_id": "exp1"}]
            state.values["experiment_results"] = []
            state.values["experiment_decision"] = {"action": "hold"}

            agent = TreeSearchAgent()
            agent.run(state, _make_context(tmp))

            tree = state.values["experiment_tree"]
            self.assertEqual(len(tree["nodes"]), 1)

    def test_generates_only_remaining_slots(self):
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            state.values["experiment_plans"] = [
                {"experiment_id": "exp1", "hypothesis": "H", "modification": "patch"}
            ]
            state.values["experiment_results"] = [
                {"result_id": "r1", "status": "unparsed"}
            ]
            state.values["experiment_decision"] = {"action": "investigate"}
            # Pre-populate with 2 existing pending nodes, leaving 1 slot
            from dataclasses import asdict
            from schemas.experiment_tree import ExperimentBranch, ExperimentNode as EN
            existing = ExperimentBranch()
            root = EN(node_id="r", experiment_id="e1", hypothesis="H", depth=0, status="active")
            child1 = EN(node_id="c1", experiment_id="e2", parent_id="r",
                        hypothesis="H1", depth=1, status="pending")
            child2 = EN(node_id="c2", experiment_id="e3", parent_id="r",
                        hypothesis="H2", depth=1, status="pending")
            existing.root_id = root.node_id
            existing.nodes = [root, child1, child2]
            state.values["experiment_tree"] = asdict(existing)

            agent = TreeSearchAgent()
            agent.run(state, _make_context(tmp))

            tree = state.values["experiment_tree"]
            # Should only add 1 new node (3 max - 2 existing = 1 remaining)
            self.assertEqual(len(tree["nodes"]), 4)

    def test_root_at_max_depth_cannot_branch(self):
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            state.values["experiment_plans"] = [
                {"experiment_id": "exp1", "hypothesis": "H"}
            ]
            state.values["experiment_results"] = [
                {"result_id": "r1", "status": "failed"}
            ]
            state.values["experiment_decision"] = {"action": "rollback"}
            # Pre-populate tree with root at depth 2
            from dataclasses import asdict
            from schemas.experiment_tree import ExperimentBranch, ExperimentNode as EN
            existing = ExperimentBranch()
            root = EN(node_id="r", experiment_id="e1", hypothesis="H", depth=2, status="active")
            existing.root_id = root.node_id
            existing.nodes = [root]
            state.values["experiment_tree"] = asdict(existing)

            agent = TreeSearchAgent()
            agent.run(state, _make_context(tmp))

            tree = state.values["experiment_tree"]
            # No branching — root at max depth
            self.assertEqual(len(tree["nodes"]), 1)

    def test_preserves_old_children_ids_on_append(self):
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            state.values["experiment_plans"] = [
                {"experiment_id": "exp1", "hypothesis": "H", "modification": "patch"}
            ]
            state.values["experiment_results"] = [
                {"result_id": "r1", "status": "unparsed"}
            ]
            state.values["experiment_decision"] = {"action": "investigate"}
            # Pre-populate with root that has 1 existing child
            from dataclasses import asdict
            from schemas.experiment_tree import ExperimentBranch, ExperimentNode as EN
            existing = ExperimentBranch()
            root = EN(
                node_id="r", experiment_id="e1", hypothesis="H", depth=0,
                status="active", children_ids=["old_child"],
            )
            old_child = EN(
                node_id="old_child", experiment_id="e_old", parent_id="r",
                hypothesis="old", depth=1, status="completed",
            )
            existing.root_id = root.node_id
            existing.nodes = [root, old_child]
            state.values["experiment_tree"] = asdict(existing)

            agent = TreeSearchAgent()
            agent.run(state, _make_context(tmp))

            tree = state.values["experiment_tree"]
            root_node = [n for n in tree["nodes"] if n["depth"] == 0][0]
            # Old child + newly added branch children
            self.assertIn("old_child", root_node["children_ids"])
            self.assertGreaterEqual(len(root_node["children_ids"]), 2)


class NodeToPlanTest(TestCase):
    def test_node_to_plan_produces_valid_plan(self):
        topic = TopicPack(
            topic_name="test_topic",
            experiment_metrics=["ADE", "FDE"],
            codebase={"repo_path": "/fake", "allowed_auto_edit": ["data/*", "models/*"]},
        )
        node = ExperimentNode(
            node_id="n1",
            experiment_id="exp_test",
            parent_id="root",
            hypothesis="Using intention conditioning may improve ADE",
            patch_scope="data loader change",
            depth=1,
            status="selected",
        )
        plan = _node_to_plan(node, topic)

        self.assertIsInstance(plan, ExperimentPlan)
        self.assertIn("intention conditioning", plan.hypothesis)
        self.assertEqual(plan.experiment_id, "exp_test")
        self.assertEqual(plan.modification, "data loader change")
        self.assertIn("data/", plan.files_to_change[0].lower() if plan.files_to_change else "")
        self.assertEqual(plan.training_config["mode"], "smoke-only")
        self.assertEqual(plan.metrics, topic.experiment_metrics)
        self.assertTrue(plan.acceptance_criteria["smoke_must_pass"])

    def test_infer_files_matches_allowed(self):
        allowed = ["models/*", "trainer/*", "data/dataloader_virat.py", "cfg/virat/*", "utils/*"]
        # "data loader" should match data/*
        result = _infer_files("data loader modification", allowed)
        self.assertTrue(any("data" in f.lower() for f in result))

        # "fusion layer" should match models/*
        result = _infer_files("fusion layer change", allowed)
        self.assertTrue(any("model" in f.lower() for f in result))

        # "config" should match cfg/*
        result = _infer_files("config adjustment", allowed)
        self.assertTrue(any("cfg" in f.lower() for f in result))

    def test_infer_files_fallback_to_first_two(self):
        allowed = ["models/*", "trainer/*"]
        result = _infer_files("unrecognized scope text", allowed)
        self.assertEqual(len(result), 2)
        self.assertEqual(result, allowed[:2])

    def test_infer_files_empty_allowed(self):
        result = _infer_files("data loader", [])
        self.assertEqual(result, [])


class BranchToPlanAgentTest(TestCase):
    def test_converts_selected_node_to_plan(self):
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            state.values["selected_branch_node"] = {
                "node_id": "n1",
                "experiment_id": "exp_test",
                "parent_id": "root",
                "hypothesis": "Using intention conditioning may improve ADE",
                "patch_scope": "data loader",
                "result": {},
                "decision": {},
                "children_ids": [],
                "status": "selected",
                "depth": 1,
            }
            agent = BranchToPlanAgent()
            result = agent.run(state, _make_context(tmp))

            self.assertIn("converted node", result.notes[0])
            plans = state.values.get("experiment_plans", [])
            self.assertEqual(len(plans), 1)
            self.assertIn("intention conditioning", plans[0]["hypothesis"])

    def test_noop_without_selected_node(self):
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            agent = BranchToPlanAgent()
            result = agent.run(state, _make_context(tmp))

            self.assertIn("no selected branch node", result.notes[0])
            self.assertNotIn("experiment_plans", state.values)

    def test_registers_artifact_on_plan(self):
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            state.values["selected_branch_node"] = {
                "node_id": "n_art",
                "experiment_id": "exp_art",
                "parent_id": "root",
                "hypothesis": "Test artifact registration",
                "patch_scope": "models/*",
                "result": {},
                "decision": {},
                "children_ids": [],
                "status": "selected",
                "depth": 1,
            }
            agent = BranchToPlanAgent()
            result = agent.run(state, _make_context(tmp))

            self.assertIn("branch_experiment_plans", result.artifacts)
            self.assertEqual(result.artifacts["branch_experiment_plans"], ["n_art"])


class TreeSearchSelectedNodeTest(TestCase):
    """Tests that TreeSearchAgent writes results to selected_branch_node, not root."""

    def test_writes_result_to_selected_node_on_pass(self):
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            state.values["experiment_tree"] = {
                "branch_id": "b1",
                "root_id": "root_1",
                "status": "active",
                "max_depth": 2,
                "max_active_nodes": 3,
                "nodes": [
                    {
                        "node_id": "root_1", "experiment_id": "e1",
                        "parent_id": "", "hypothesis": "Root H",
                        "patch_scope": "", "result": {}, "decision": {},
                        "children_ids": ["child_sel"],
                        "status": "active", "depth": 0,
                    },
                    {
                        "node_id": "child_sel", "experiment_id": "e2",
                        "parent_id": "root_1", "hypothesis": "Branch H",
                        "patch_scope": "data loader",
                        "result": {}, "decision": {}, "children_ids": [],
                        "status": "selected", "depth": 1,
                    },
                ],
            }
            state.values["selected_branch_node"] = {
                "node_id": "child_sel",
                "experiment_id": "e2",
                "parent_id": "root_1",
                "hypothesis": "Branch H",
                "patch_scope": "data loader",
                "result": {}, "decision": {}, "children_ids": [],
                "status": "selected", "depth": 1,
            }
            state.values["experiment_results"] = [
                {"result_id": "r1", "status": "passed", "metrics": {"ade": 0.15}}
            ]
            state.values["experiment_decision"] = {"action": "continue"}

            agent = TreeSearchAgent()
            agent.run(state, _make_context(tmp))

            tree = state.values["experiment_tree"]
            selected_node = [n for n in tree["nodes"] if n["node_id"] == "child_sel"][0]
            root_node = [n for n in tree["nodes"] if n["node_id"] == "root_1"][0]

            # Selected node gets result and decision
            self.assertEqual(selected_node["result"], {"result_id": "r1", "status": "passed", "metrics": {"ade": 0.15}})
            self.assertEqual(selected_node["decision"], {"action": "continue"})
            self.assertEqual(selected_node["status"], "smoke_passed")
            # Root is not modified to smoke_passed
            self.assertEqual(root_node["status"], "active")

    def test_branches_from_selected_node_on_fail(self):
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            state.values["experiment_tree"] = {
                "branch_id": "b2",
                "root_id": "root_2",
                "status": "active",
                "max_depth": 2,
                "max_active_nodes": 3,
                "nodes": [
                    {
                        "node_id": "root_2", "experiment_id": "e1",
                        "parent_id": "", "hypothesis": "Root H",
                        "patch_scope": "", "result": {}, "decision": {},
                        "children_ids": ["child_fail"],
                        "status": "active", "depth": 0,
                    },
                    {
                        "node_id": "child_fail", "experiment_id": "e2",
                        "parent_id": "root_2", "hypothesis": "Failed branch",
                        "patch_scope": "fusion layer",
                        "result": {}, "decision": {}, "children_ids": [],
                        "status": "selected", "depth": 1,
                    },
                ],
            }
            state.values["selected_branch_node"] = {
                "node_id": "child_fail",
                "experiment_id": "e2",
                "parent_id": "root_2",
                "hypothesis": "Failed branch",
                "patch_scope": "fusion layer",
                "result": {}, "decision": {}, "children_ids": [],
                "status": "selected", "depth": 1,
            }
            state.values["experiment_results"] = [
                {"result_id": "r1", "status": "failed"}
            ]
            state.values["experiment_decision"] = {"action": "rollback", "reason": "failed"}

            agent = TreeSearchAgent()
            agent.run(state, _make_context(tmp))

            tree = state.values["experiment_tree"]
            selected_node = [n for n in tree["nodes"] if n["node_id"] == "child_fail"][0]
            root_node = [n for n in tree["nodes"] if n["node_id"] == "root_2"][0]

            # Selected node got result, decision, and status update
            self.assertEqual(selected_node["result"], {"result_id": "r1", "status": "failed"})
            self.assertEqual(selected_node["decision"], {"action": "rollback", "reason": "failed"})
            self.assertEqual(selected_node["status"], "branched")
            # New children hang from selected node, not root
            self.assertGreaterEqual(len(selected_node["children_ids"]), 1)
            # Root children unchanged (still only has the selected node)
            self.assertEqual(root_node["children_ids"], ["child_fail"])

    def test_reverts_selected_to_pending_when_no_results(self):
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            state.values["experiment_tree"] = {
                "branch_id": "b3",
                "root_id": "root_3",
                "status": "active",
                "max_depth": 2,
                "max_active_nodes": 3,
                "nodes": [
                    {
                        "node_id": "root_3", "experiment_id": "e1",
                        "parent_id": "", "hypothesis": "Root",
                        "patch_scope": "", "result": {}, "decision": {},
                        "children_ids": ["child_stuck"],
                        "status": "active", "depth": 0,
                    },
                    {
                        "node_id": "child_stuck", "experiment_id": "e2",
                        "parent_id": "root_3", "hypothesis": "Stuck branch",
                        "patch_scope": "config",
                        "result": {}, "decision": {}, "children_ids": [],
                        "status": "selected", "depth": 1,
                    },
                ],
            }
            state.values["selected_branch_node"] = {
                "node_id": "child_stuck",
                "experiment_id": "e2",
                "parent_id": "root_3",
                "hypothesis": "Stuck branch",
                "patch_scope": "config",
                "result": {}, "decision": {}, "children_ids": [],
                "status": "selected", "depth": 1,
            }
            # No experiment results (experiments not enabled)
            state.values["experiment_results"] = []
            state.values["experiment_decision"] = {"action": "hold"}

            agent = TreeSearchAgent()
            agent.run(state, _make_context(tmp))

            tree = state.values["experiment_tree"]
            stuck_node = [n for n in tree["nodes"] if n["node_id"] == "child_stuck"][0]
            # Reverted to pending so it can be reselected next run
            self.assertEqual(stuck_node["status"], "pending")

    def test_mixed_results_per_node_processing(self):
        """passed node → smoke_passed; unparsed node → branched (Fix 1 regression)."""
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            state.values["experiment_tree"] = {
                "branch_id": "b1",
                "root_id": "root",
                "status": "active",
                "max_depth": 2,
                "max_active_nodes": 3,
                "nodes": [
                    {
                        "node_id": "root", "experiment_id": "e_root",
                        "parent_id": "", "hypothesis": "Root",
                        "patch_scope": "", "result": {}, "decision": {},
                        "children_ids": ["node_pass", "node_unparsed"],
                        "status": "active", "depth": 0,
                    },
                    {
                        "node_id": "node_pass", "experiment_id": "exp_pass",
                        "parent_id": "root", "hypothesis": "Pass branch",
                        "patch_scope": "data loader",
                        "result": {}, "decision": {}, "children_ids": [],
                        "status": "selected", "depth": 1,
                    },
                    {
                        "node_id": "node_unparsed", "experiment_id": "exp_unparsed",
                        "parent_id": "root", "hypothesis": "Unparsed branch",
                        "patch_scope": "fusion layer",
                        "result": {}, "decision": {}, "children_ids": [],
                        "status": "selected", "depth": 1,
                    },
                ],
            }
            state.values["selected_branch_nodes"] = [
                {"node_id": "node_pass", "experiment_id": "exp_pass"},
                {"node_id": "node_unparsed", "experiment_id": "exp_unparsed"},
            ]
            state.values["selected_branch_node"] = state.values["selected_branch_nodes"][0]
            # Mixed results: one passed, one unparsed
            state.values["experiment_results"] = [
                {"result_id": "r1", "experiment_id": "exp_pass", "status": "passed", "metrics": {"ade": 0.15}},
                {"result_id": "r2", "experiment_id": "exp_unparsed", "status": "unparsed", "metrics": {}},
            ]
            # Per-experiment decisions
            state.values["experiment_decisions"] = {
                "exp_pass": {"action": "continue", "reason": "passed"},
                "exp_unparsed": {"action": "investigate", "reason": "no metrics"},
            }
            state.values["experiment_decision"] = {"action": "continue"}

            agent = TreeSearchAgent()
            agent.run(state, _make_context(tmp))

            tree = state.values["experiment_tree"]
            node_pass = [n for n in tree["nodes"] if n["node_id"] == "node_pass"][0]
            node_unparsed = [n for n in tree["nodes"] if n["node_id"] == "node_unparsed"][0]

            # Passed node → smoke_passed
            self.assertEqual(node_pass["status"], "smoke_passed")
            self.assertEqual(node_pass["result"]["status"], "passed")
            # Unparsed node → branched (generates children)
            self.assertEqual(node_unparsed["status"], "branched")
            self.assertGreaterEqual(len(node_unparsed["children_ids"]), 1)

    def test_reverts_all_selected_when_no_results(self):
        """Multi-branch: ALL selected nodes reverted to pending (Fix 2 regression)."""
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            state.values["experiment_tree"] = {
                "branch_id": "b_multi",
                "root_id": "r",
                "status": "active",
                "max_depth": 2,
                "max_active_nodes": 3,
                "nodes": [
                    {
                        "node_id": "r", "experiment_id": "e1",
                        "parent_id": "", "hypothesis": "Root",
                        "patch_scope": "", "result": {}, "decision": {},
                        "children_ids": ["sel_a", "sel_b"],
                        "status": "active", "depth": 0,
                    },
                    {
                        "node_id": "sel_a", "experiment_id": "ea",
                        "parent_id": "r", "hypothesis": "Branch A",
                        "patch_scope": "config",
                        "result": {}, "decision": {}, "children_ids": [],
                        "status": "selected", "depth": 1,
                    },
                    {
                        "node_id": "sel_b", "experiment_id": "eb",
                        "parent_id": "r", "hypothesis": "Branch B",
                        "patch_scope": "fusion",
                        "result": {}, "decision": {}, "children_ids": [],
                        "status": "selected", "depth": 1,
                    },
                ],
            }
            state.values["selected_branch_nodes"] = [
                {"node_id": "sel_a"}, {"node_id": "sel_b"},
            ]
            state.values["selected_branch_node"] = {"node_id": "sel_a"}
            state.values["experiment_results"] = []

            agent = TreeSearchAgent()
            agent.run(state, _make_context(tmp))

            tree = state.values["experiment_tree"]
            sel_a = [n for n in tree["nodes"] if n["node_id"] == "sel_a"][0]
            sel_b = [n for n in tree["nodes"] if n["node_id"] == "sel_b"][0]
            self.assertEqual(sel_a["status"], "pending")
            self.assertEqual(sel_b["status"], "pending")

    def test_two_failed_nodes_both_branch_with_slots(self):
        """Two failed selected nodes with available slots → both get branched (Fix 3 regression)."""
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            state.values["experiment_tree"] = {
                "branch_id": "b_slots",
                "root_id": "root",
                "status": "active",
                "max_depth": 3,
                "max_active_nodes": 2,
                "nodes": [
                    {
                        "node_id": "root", "experiment_id": "e_root",
                        "parent_id": "", "hypothesis": "Root",
                        "patch_scope": "", "result": {}, "decision": {},
                        "children_ids": ["fail_a", "fail_b"],
                        "status": "active", "depth": 0,
                    },
                    {
                        "node_id": "fail_a", "experiment_id": "ea",
                        "parent_id": "root", "hypothesis": "Fail A",
                        "patch_scope": "data loader",
                        "result": {}, "decision": {}, "children_ids": [],
                        "status": "selected", "depth": 1,
                    },
                    {
                        "node_id": "fail_b", "experiment_id": "eb",
                        "parent_id": "root", "hypothesis": "Fail B",
                        "patch_scope": "fusion layer",
                        "result": {}, "decision": {}, "children_ids": [],
                        "status": "selected", "depth": 1,
                    },
                ],
            }
            state.values["selected_branch_nodes"] = [
                {"node_id": "fail_a", "experiment_id": "ea"},
                {"node_id": "fail_b", "experiment_id": "eb"},
            ]
            state.values["selected_branch_node"] = state.values["selected_branch_nodes"][0]
            state.values["experiment_results"] = [
                {"result_id": "r1", "experiment_id": "ea", "status": "failed"},
                {"result_id": "r2", "experiment_id": "eb", "status": "failed"},
            ]
            state.values["experiment_decisions"] = {
                "ea": {"action": "rollback", "reason": "failed"},
                "eb": {"action": "rollback", "reason": "failed"},
            }
            state.values["experiment_decision"] = {"action": "rollback"}

            agent = TreeSearchAgent()
            agent.run(state, _make_context(tmp))

            tree = state.values["experiment_tree"]
            fail_a = [n for n in tree["nodes"] if n["node_id"] == "fail_a"][0]
            fail_b = [n for n in tree["nodes"] if n["node_id"] == "fail_b"][0]

            # Both failed nodes should be branched (max_active=2, 0 pending → 2 slots)
            self.assertEqual(fail_a["status"], "branched")
            self.assertEqual(fail_b["status"], "branched")


if __name__ == "__main__":
    main()
