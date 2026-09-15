from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from agents.experiment_orchestrator import ExperimentOrchestratorAgent
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState
from schemas.topic_pack import TopicPack


def _make_state(**kwargs) -> ResearchState:
    topic = TopicPack(topic_name="test", codebase=kwargs.pop("codebase", {"repo_path": "/fake/repo", "allowed_auto_edit": ["model/"]}))
    state = ResearchState(topic=topic)
    state.values["experiment_plans"] = kwargs.pop("plans", [{"experiment_id": "exp_1", "hypothesis": "test", "modification": "change", "files_to_change": ["model/test.py"]}])
    state.values["code_tasks"] = [{"task_id": "ct_1", "experiment_id": "exp_1", "allowed_paths": ["model/"], "protected_paths": []}]
    return state


class ExperimentOrchestratorAgentTest(TestCase):
    def test_skips_when_experiments_disabled(self):
        with TemporaryDirectory() as tmp:
            state = _make_state()
            context = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None, tool_registry=None,
                settings={"enable_experiments": False, "enable_code_writes": False, "enable_llm": False, "max_debug_attempts": 3},
            )
            agent = ExperimentOrchestratorAgent()
            result = agent.run(state, context)
            self.assertEqual(state.values.get("experiment_results"), [])
            self.assertIn("skipped", result.notes[0])

    def test_executes_smoke_when_code_writes_disabled(self):
        with TemporaryDirectory() as tmp:
            state = _make_state()
            context = AgentContext(
                artifact_store=ArtifactStore(Path(tmp) / "runs"),
                memory_store=None, tool_registry=None,
                settings={"enable_experiments": True, "enable_code_writes": False, "enable_llm": False, "max_debug_attempts": 3},
            )
            agent = ExperimentOrchestratorAgent()
            result = agent.run(state, context)
            patches = state.values.get("code_patches_by_experiment_id", {})
            self.assertEqual(patches.get("exp_1", {}).get("status"), "skipped")
            self.assertIsInstance(state.values.get("experiment_results"), list)

    def test_multi_plan_isolation(self):
        with TemporaryDirectory() as tmp:
            state = _make_state(plans=[
                {"experiment_id": "exp_1", "hypothesis": "h1", "modification": "m1", "files_to_change": ["model/a.py"]},
                {"experiment_id": "exp_2", "hypothesis": "h2", "modification": "m2", "files_to_change": ["model/b.py"]},
            ])
            state.values["code_tasks"] = [
                {"task_id": "ct_1", "experiment_id": "exp_1", "allowed_paths": ["model/"], "protected_paths": []},
                {"task_id": "ct_2", "experiment_id": "exp_2", "allowed_paths": ["model/"], "protected_paths": []},
            ]
            context = AgentContext(
                artifact_store=ArtifactStore(Path(tmp) / "runs"),
                memory_store=None, tool_registry=None,
                settings={"enable_experiments": True, "enable_code_writes": False, "enable_llm": False, "max_debug_attempts": 3},
            )
            agent = ExperimentOrchestratorAgent()
            agent.run(state, context)
            patches = state.values.get("code_patches_by_experiment_id", {})
            self.assertIn("exp_1", patches)
            self.assertIn("exp_2", patches)
            self.assertNotEqual(patches["exp_1"].get("experiment_id"), patches["exp_2"].get("experiment_id"))


if __name__ == "__main__":
    main()
