from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from agents.method_card_retriever import MethodCardRetrieverAgent
from agents.opportunity_agent import OpportunityAgent
from agents.experiment_planner import ExperimentPlannerAgent
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState
from memory.literature_memory import LiteratureMemoryStore
from schemas.topic_pack import TopicPack


def _make_topic(name: str = "test_topic") -> TopicPack:
    return TopicPack(
        topic_name=name,
        domain={"primary_area": "pedestrian_trajectory_prediction"},
        current_status={"datasets": ["VIRAT"], "data_requirement": "existing data"},
        experiment_metrics=["ADE", "FDE"],
        search_seeds={"keywords": ["diffusion", "trajectory"]},
        codebase={"repo_path": "/fake"},
    )


def _make_context(tmp_path: str) -> AgentContext:
    return AgentContext(
        artifact_store=ArtifactStore(Path(tmp_path)),
        memory_store=None,  # type: ignore
        tool_registry=None,  # type: ignore
        settings={},
    )


def _make_card(method_id: str, paper_id: str, **overrides) -> dict:
    card = {
        "method_card_id": method_id,
        "paper_id": paper_id,
        "task": "pedestrian trajectory prediction",
        "problem_setting": "multimodal",
        "input_modalities": ["trajectory", "intention"],
        "model_architecture": {"type": "diffusion"},
        "fusion_strategy": {"type": "cross-attention"},
        "training_objective": "minADE",
        "datasets": ["VIRAT"],
        "metrics": ["ADE", "FDE"],
        "main_results": "ADE=0.23",
        "limitations": [],
        "reusable_ideas_for_current_topic": [],
        "implementation_difficulty": "medium",
        "risk": [],
        "evidence_ids": [],
    }
    card.update(overrides)
    return card


class MethodCardRetrieverAgentTest(TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "test.db"
        self.store = LiteratureMemoryStore(self.db_path)
        self.agent = MethodCardRetrieverAgent(lit_memory_store=self.store)

    def tearDown(self):
        self.tmp.cleanup()

    def test_retrieves_historical_cards(self):
        scope = "test_topic"
        self.store.write_method_card(
            _make_card("m1", "p_old", task="pedestrian_trajectory_prediction"), scope
        )
        self.store.write_method_card(
            _make_card("m2", "p_old2", task="pedestrian_trajectory_prediction"), scope
        )

        topic = _make_topic("test_topic")
        state = ResearchState(topic=topic)
        state.values["selected_papers"] = [{"paper_id": "p_current"}]
        result = self.agent.run(state, _make_context(self.tmp.name))

        self.assertEqual(len(state.values["historical_method_cards"]), 2)
        self.assertIn("retrieved 2", result.notes[0])

    def test_deduplicates_current_run_papers(self):
        scope = "test_topic"
        self.store.write_method_card(
            _make_card("m1", "p_same", task="pedestrian_trajectory_prediction"), scope
        )

        topic = _make_topic("test_topic")
        state = ResearchState(topic=topic)
        state.values["selected_papers"] = [{"paper_id": "p_same"}]
        self.agent.run(state, _make_context(self.tmp.name))

        self.assertEqual(len(state.values["historical_method_cards"]), 0)

    def test_no_results_when_memory_empty(self):
        topic = _make_topic("test_topic")
        state = ResearchState(topic=topic)
        self.agent.run(state, _make_context(self.tmp.name))
        self.assertEqual(state.values["historical_method_cards"], [])
        self.assertEqual(state.values["historical_method_card_count"], 0)

    def test_scope_isolation(self):
        self.store.write_method_card(
            _make_card("m_a", "p_a", task="pedestrian_trajectory_prediction"), "scope_A"
        )
        topic = _make_topic("different_topic")
        state = ResearchState(topic=topic)
        self.agent.run(state, _make_context(self.tmp.name))
        self.assertEqual(len(state.values["historical_method_cards"]), 0)

    def test_noop_when_no_store(self):
        agent = MethodCardRetrieverAgent(lit_memory_store=None)
        topic = _make_topic()
        state = ResearchState(topic=topic)
        result = agent.run(state, _make_context(self.tmp.name))
        self.assertIn("skipped", result.notes[0])
        self.assertEqual(state.values["historical_method_cards"], [])


class OpportunityAgentWithHistoricalCardsTest(TestCase):
    def test_opportunity_enriched_with_historical_data(self):
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            state.values["codebase_report"] = {}
            state.values["selected_papers"] = [
                {"paper_id": "p1", "title": "Test Paper"}
            ]
            state.values["historical_method_cards"] = [
                {
                    "method_card_id": "h1",
                    "paper_id": "old_paper",
                    "task": "trajectory prediction",
                    "datasets": ["VIRAT", "ETH/UCY"],
                    "metrics": ["ADE"],
                    "reusable_ideas_for_current_topic": [
                        "intention conditioning reduces ADE by 15%",
                    ],
                },
            ]
            context = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None,  # type: ignore
                tool_registry=None,  # type: ignore
                settings={},
            )
            agent = OpportunityAgent()
            agent.run(state, context)

            opp = state.values["opportunities"][0]
            self.assertIn("Historical insights", opp["technical_strategy"])
            self.assertIn("intention conditioning", opp["technical_strategy"])
            self.assertIn("historical", opp["data_requirement"])

    def test_opportunity_noop_without_historical_cards(self):
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            state.values["codebase_report"] = {}
            state.values["selected_papers"] = [{"paper_id": "p1"}]
            state.values["historical_method_cards"] = []
            context = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None,  # type: ignore
                tool_registry=None,  # type: ignore
                settings={},
            )
            agent = OpportunityAgent()
            agent.run(state, context)

            opp = state.values["opportunities"][0]
            self.assertNotIn("Historical insights", opp["technical_strategy"])


class ExperimentPlannerAgentWithHistoricalCardsTest(TestCase):
    def test_plan_includes_historical_metrics(self):
        topic = _make_topic()
        topic.experiment_metrics = ["FDE"]
        state = ResearchState(topic=topic)
        state.values["opportunities"] = [{"title": "Test", "hypothesis": "H", "technical_strategy": "S"}]
        state.values["codebase_report"] = {}
        state.values["historical_method_cards"] = [
            {"metrics": ["ADE", "miss_rate"], "reusable_ideas_for_current_topic": []},
        ]

        agent = ExperimentPlannerAgent()
        plan = agent._rule_based_plan(state)

        self.assertIn("FDE", plan.metrics)
        self.assertIn("ADE", plan.metrics)

    def test_llm_messages_include_historical_cards(self):
        topic = _make_topic()
        state = ResearchState(topic=topic)
        state.values["opportunities"] = [{"title": "Test", "hypothesis": "H"}]
        state.values["codebase_report"] = {}
        state.values["method_cards"] = [{"method_card_id": "m1", "task": "current"}]
        state.values["historical_method_cards"] = [{"method_card_id": "h1", "task": "historical"}]

        agent = ExperimentPlannerAgent()
        from dataclasses import asdict
        from schemas.experiment_plan import ExperimentPlan
        base = ExperimentPlan(name="test", hypothesis="H")
        messages = agent._build_llm_messages(state, base)
        content = messages[1]["content"]
        self.assertIn("current", content)
        self.assertIn("historical", content)


if __name__ == "__main__":
    main()
