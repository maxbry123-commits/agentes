from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from agents.tree_search_agent import TreeSearchAgent
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState


def _make_topic():
    from schemas.topic_pack import TopicPack
    return TopicPack(topic_name="test_promo", experiment_metrics=["ADE", "FDE"])


class AutoPromotionTest(TestCase):
    def test_auto_promotes_when_both_metrics_better(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_make_topic())
            state.values["experiment_tree"] = {
                "branch_id": "promo1", "root_id": "root_p",
                "status": "active", "max_depth": 2, "max_active_nodes": 3,
                "nodes": [
                    {
                        "node_id": "root_p", "parent_id": "", "hypothesis": "Old root",
                        "children_ids": ["better"], "status": "active",
                        "result": {"status": "passed", "metrics": {"ade": 0.5, "fde": 0.3}},
                        "decision": {"action": "continue"}, "depth": 0,
                    },
                    {
                        "node_id": "better", "experiment_id": "exp_better",
                        "parent_id": "root_p", "hypothesis": "Better one",
                        "patch_scope": "data", "children_ids": [],
                        "status": "selected", "result": {}, "decision": {}, "depth": 1,
                    },
                ],
            }
            state.values["selected_branch_node"] = {
                "node_id": "better", "experiment_id": "exp_better",
                "parent_id": "root_p", "hypothesis": "Better one",
                "patch_scope": "data", "children_ids": [],
                "status": "selected", "result": {}, "decision": {}, "depth": 1,
            }
            state.values["experiment_results"] = [
                {"result_id": "r1", "status": "passed",
                 "metrics": {"ade": 0.2, "fde": 0.1}}
            ]
            state.values["experiment_decision"] = {"action": "continue"}

            ctx = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None, tool_registry=None, settings={},
            )
            agent = TreeSearchAgent()
            result = agent.run(state, ctx)

            tree = state.values["experiment_tree"]
            self.assertEqual(tree["root_id"], "better")
            root = next(n for n in tree["nodes"] if n["node_id"] == "better")
            self.assertEqual(root["status"], "active")
            old = next(n for n in tree["nodes"] if n["node_id"] == "root_p")
            self.assertEqual(old["status"], "archived")
            # Check notes mention auto-promotion
            self.assertTrue(any("auto-promoted" in n for n in result.notes))

    def test_no_auto_promote_when_only_one_metric_better(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_make_topic())
            state.values["experiment_tree"] = {
                "branch_id": "promo2", "root_id": "root_q",
                "status": "active", "max_depth": 2, "max_active_nodes": 3,
                "nodes": [
                    {
                        "node_id": "root_q", "parent_id": "", "hypothesis": "R",
                        "children_ids": ["border"], "status": "active",
                        "result": {"status": "passed", "metrics": {"ade": 0.3, "fde": 0.1}},
                        "decision": {}, "depth": 0,
                    },
                    {
                        "node_id": "border", "experiment_id": "exp_border",
                        "parent_id": "root_q", "hypothesis": "Border",
                        "patch_scope": "cfg", "children_ids": [],
                        "status": "selected", "result": {}, "decision": {}, "depth": 1,
                    },
                ],
            }
            state.values["selected_branch_node"] = {
                "node_id": "border", "parent_id": "root_q",
                "status": "selected", "result": {}, "decision": {}, "depth": 1,
            }
            # ADE better (0.2 < 0.3) but FDE worse (0.3 > 0.1)
            state.values["experiment_results"] = [
                {"result_id": "r2", "status": "passed",
                 "metrics": {"ade": 0.2, "fde": 0.3}}
            ]
            state.values["experiment_decision"] = {"action": "continue"}

            ctx = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None, tool_registry=None, settings={},
            )
            agent = TreeSearchAgent()
            result = agent.run(state, ctx)

            tree = state.values["experiment_tree"]
            # Root unchanged
            self.assertEqual(tree["root_id"], "root_q")
            # Borderline in notes
            self.assertTrue(any("borderline" in n for n in result.notes))

    def test_auto_promote_clears_parent_id(self):
        """Promoted node has parent_id cleared; old root becomes historical child."""
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_make_topic())
            state.values["experiment_tree"] = {
                "branch_id": "promo3", "root_id": "root_r",
                "status": "active", "max_depth": 2, "max_active_nodes": 3,
                "nodes": [
                    {
                        "node_id": "root_r", "parent_id": "", "hypothesis": "Old",
                        "children_ids": ["new_root"], "status": "active",
                        "result": {"status": "passed", "metrics": {"ade": 0.5, "fde": 0.4}},
                        "decision": {"action": "continue"}, "depth": 0,
                    },
                    {
                        "node_id": "new_root", "experiment_id": "exp_nr",
                        "parent_id": "root_r", "hypothesis": "New root",
                        "patch_scope": "data", "children_ids": [],
                        "status": "selected", "result": {}, "decision": {}, "depth": 1,
                    },
                ],
            }
            state.values["selected_branch_node"] = {
                "node_id": "new_root", "parent_id": "root_r",
                "status": "selected", "result": {}, "decision": {}, "depth": 1,
            }
            state.values["experiment_results"] = [
                {"result_id": "r3", "status": "passed",
                 "metrics": {"ade": 0.1, "fde": 0.2}}
            ]
            state.values["experiment_decision"] = {"action": "continue"}

            ctx = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None, tool_registry=None, settings={},
            )
            agent = TreeSearchAgent()
            agent.run(state, ctx)

            tree = state.values["experiment_tree"]
            self.assertEqual(tree["root_id"], "new_root")
            new_root = next(n for n in tree["nodes"] if n["node_id"] == "new_root")
            old_root = next(n for n in tree["nodes"] if n["node_id"] == "root_r")
            # New root has no parent
            self.assertEqual(new_root["parent_id"], "")
            self.assertEqual(new_root["status"], "active")
            self.assertEqual(new_root["depth"], 0)
            # Old root is archived, parented to new root, depth 1
            self.assertEqual(old_root["status"], "archived")
            self.assertEqual(old_root["parent_id"], "new_root")
            self.assertEqual(old_root["children_ids"], [])
            self.assertEqual(old_root["depth"], 1)
            # New root has old root in children_ids
            self.assertIn("root_r", new_root["children_ids"])


if __name__ == "__main__":
    main()
