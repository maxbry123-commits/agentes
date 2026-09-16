from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from agents.tree_search_agent import BranchToPlanAgent
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState


def _make_topic():
    from schemas.topic_pack import TopicPack
    return TopicPack(
        topic_name="test_multi",
        codebase={"repo_path": "/fake", "allowed_auto_edit": ["data/*", "models/*", "cfg/*"]},
        experiment_metrics=["ADE", "FDE"],
    )


class MultiPlanTest(TestCase):
    def test_two_selected_branches_produce_two_plans(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_make_topic())
            state.values["experiment_tree"] = {
                "branch_id": "mpt", "root_id": "r",
                "status": "active", "max_depth": 2, "max_active_nodes": 3,
                "nodes": [
                    {"node_id": "r", "parent_id": "", "hypothesis": "R",
                     "children_ids": ["a1", "a2"], "status": "active",
                     "result": {}, "decision": {}, "depth": 0},
                    {"node_id": "a1", "experiment_id": "exp_a1",
                     "parent_id": "r", "hypothesis": "A1",
                     "patch_scope": "data loader", "children_ids": [],
                     "status": "selected", "result": {}, "decision": {}, "depth": 1},
                    {"node_id": "a2", "experiment_id": "exp_a2",
                     "parent_id": "r", "hypothesis": "A2",
                     "patch_scope": "config", "children_ids": [],
                     "status": "selected", "result": {}, "decision": {}, "depth": 1},
                ],
            }
            state.values["selected_branch_nodes"] = [
                n for n in state.values["experiment_tree"]["nodes"]
                if n["status"] == "selected"
            ]

            ctx = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None, tool_registry=None, settings={},
            )
            agent = BranchToPlanAgent()
            result = agent.run(state, ctx)

            plans = state.values.get("experiment_plans", [])
            self.assertEqual(len(plans), 2)
            plan_ids = [p["experiment_id"] for p in plans]
            self.assertIn("exp_a1", plan_ids)
            self.assertIn("exp_a2", plan_ids)
            # Artifact registered
            self.assertIn("branch_experiment_plans", result.artifacts)
            self.assertEqual(len(result.artifacts["branch_experiment_plans"]), 2)

    def test_no_selected_nodes_noops(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_make_topic())
            ctx = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None, tool_registry=None, settings={},
            )
            agent = BranchToPlanAgent()
            result = agent.run(state, ctx)
            self.assertIn("no selected branch", result.notes[0].lower())


class AutonomousMultiExperimentTest(TestCase):
    def test_skip_when_not_enabled(self):
        with TemporaryDirectory() as tmp:
            from agents.autonomous_experiment import AutonomousExperimentAgent
            topic = _make_topic()
            state = ResearchState(topic=topic)
            state.values["experiment_plans"] = [{"experiment_id": "e1"}]
            ctx = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None, tool_registry=None,
                settings={"enable_experiments": False},
            )
            agent = AutonomousExperimentAgent()
            result = agent.run(state, ctx)
            self.assertIn("not set", result.notes[0].lower())


if __name__ == "__main__":
    main()
