from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from agents.experiment_decision import ExperimentDecisionAgent
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState
from schemas.topic_pack import TopicPack


def _make_state(results: list[dict] | None) -> ResearchState:
    topic = TopicPack(topic_name="test")
    state = ResearchState(topic=topic)
    state.values["experiment_plans"] = [{"experiment_id": "experiment_test1"}]
    state.values["experiment_results"] = results
    return state


def _make_context(tmp_path: str) -> AgentContext:
    return AgentContext(
        artifact_store=ArtifactStore(Path(tmp_path)),
        memory_store=None,  # type: ignore
        tool_registry=None,  # type: ignore
        settings={},
    )


class ExperimentDecisionAgentTest(TestCase):
    def test_hold_when_no_results(self):
        state = _make_state(None)
        with TemporaryDirectory() as tmp:
            agent = ExperimentDecisionAgent()
            result = agent.run(state, _make_context(tmp))
            decision = state.values["experiment_decision"]
            self.assertEqual(decision["action"], "hold")

    def test_hold_when_empty_results(self):
        state = _make_state([])
        with TemporaryDirectory() as tmp:
            agent = ExperimentDecisionAgent()
            agent.run(state, _make_context(tmp))
            decision = state.values["experiment_decision"]
            self.assertEqual(decision["action"], "hold")

    def test_continue_when_all_passed(self):
        state = _make_state([
            {"result_id": "r1", "status": "passed", "metrics": {"ade": 0.30}},
            {"result_id": "r2", "status": "passed", "metrics": {"fde": 0.60}},
        ])
        with TemporaryDirectory() as tmp:
            agent = ExperimentDecisionAgent()
            agent.run(state, _make_context(tmp))
            decision = state.values["experiment_decision"]
            self.assertEqual(decision["action"], "continue")

    def test_investigate_on_error(self):
        state = _make_state([
            {"result_id": "r1", "status": "passed", "metrics": {}},
            {"result_id": "r2", "status": "error", "error_message": "CUDA OOM"},
        ])
        with TemporaryDirectory() as tmp:
            agent = ExperimentDecisionAgent()
            agent.run(state, _make_context(tmp))
            decision = state.values["experiment_decision"]
            self.assertEqual(decision["action"], "investigate")

    def test_rollback_on_failure(self):
        state = _make_state([
            {"result_id": "r1", "status": "failed", "metrics": {"ade": 0.90}},
        ])
        with TemporaryDirectory() as tmp:
            agent = ExperimentDecisionAgent()
            agent.run(state, _make_context(tmp))
            decision = state.values["experiment_decision"]
            self.assertEqual(decision["action"], "rollback")

    def test_investigate_on_unparsed(self):
        state = _make_state([
            {"result_id": "r1", "status": "unparsed", "metrics": {}},
        ])
        with TemporaryDirectory() as tmp:
            agent = ExperimentDecisionAgent()
            agent.run(state, _make_context(tmp))
            decision = state.values["experiment_decision"]
            self.assertEqual(decision["action"], "investigate")

    def test_artifact_persisted(self):
        state = _make_state([
            {"result_id": "r1", "status": "passed", "metrics": {"ade": 0.42}},
        ])
        with TemporaryDirectory() as tmp:
            context = _make_context(tmp)
            agent = ExperimentDecisionAgent()
            agent.run(state, context)
            files = context.artifact_store.list_artifacts(
                state.run_id, "experiment_decisions"
            )
            self.assertEqual(len(files), 1)

    def test_error_takes_priority_over_failure(self):
        state = _make_state([
            {"result_id": "r1", "status": "failed", "metrics": {}},
            {"result_id": "r2", "status": "error", "error_message": "timeout"},
        ])
        with TemporaryDirectory() as tmp:
            agent = ExperimentDecisionAgent()
            agent.run(state, _make_context(tmp))
            decision = state.values["experiment_decision"]
            self.assertEqual(decision["action"], "investigate")

    def test_per_experiment_decisions_mixed_results(self):
        """Mixed passed+unparsed across different experiment_ids → per-exp decisions."""
        state = ResearchState(topic=TopicPack(topic_name="test"))
        state.values["experiment_plans"] = [
            {"experiment_id": "exp_a"},
            {"experiment_id": "exp_b"},
        ]
        state.values["experiment_results"] = [
            {"result_id": "r1", "experiment_id": "exp_a", "status": "passed", "metrics": {"ade": 0.30}},
            {"result_id": "r2", "experiment_id": "exp_b", "status": "unparsed", "metrics": {}},
        ]
        with TemporaryDirectory() as tmp:
            agent = ExperimentDecisionAgent()
            agent.run(state, _make_context(tmp))
            decisions = state.values["experiment_decisions"]
            self.assertIn("exp_a", decisions)
            self.assertIn("exp_b", decisions)
            self.assertEqual(decisions["exp_a"]["action"], "continue")
            self.assertEqual(decisions["exp_b"]["action"], "investigate")

    def test_per_experiment_decisions_single_result(self):
        """Single result still produces experiment_decisions dict."""
        state = _make_state([
            {"result_id": "r1", "experiment_id": "exp_single", "status": "passed", "metrics": {"ade": 0.42}},
        ])
        with TemporaryDirectory() as tmp:
            agent = ExperimentDecisionAgent()
            agent.run(state, _make_context(tmp))
            decisions = state.values["experiment_decisions"]
            self.assertIn("exp_single", decisions)
            self.assertEqual(decisions["exp_single"]["action"], "continue")
            # Backward compat: experiment_decision also set
            self.assertEqual(state.values["experiment_decision"]["action"], "continue")

    def test_same_experiment_mixed_passed_unparsed_returns_investigate(self):
        """Unparsed takes priority over passed within the same experiment (Fix 1 regression)."""
        state = _make_state([
            {"result_id": "r1", "experiment_id": "exp_x", "status": "passed", "metrics": {"ade": 0.30}},
            {"result_id": "r2", "experiment_id": "exp_x", "status": "unparsed", "metrics": {}},
        ])
        with TemporaryDirectory() as tmp:
            agent = ExperimentDecisionAgent()
            agent.run(state, _make_context(tmp))
            decisions = state.values["experiment_decisions"]
            self.assertIn("exp_x", decisions)
            self.assertEqual(decisions["exp_x"]["action"], "investigate")


if __name__ == "__main__":
    main()
