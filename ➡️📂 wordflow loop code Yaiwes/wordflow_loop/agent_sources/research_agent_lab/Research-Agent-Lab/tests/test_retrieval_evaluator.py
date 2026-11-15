from __future__ import annotations

from unittest import TestCase, main

from pathlib import Path
from tempfile import TemporaryDirectory

from agents.retrieval_evaluator import RetrievalEvaluationAgent
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState
from schemas.retrieval_evaluation import (
    RetrievalEvaluationCheck,
    RetrievalEvaluationReport,
    RetrievalJudgement,
)
from schemas.topic_pack import TopicPack
from tools.llm_client import LLMResponse


class RetrievalEvaluationSchemaTest(TestCase):
    def test_report_defaults(self):
        check = RetrievalEvaluationCheck(
            name="paper_count",
            status="pass",
            severity="info",
            message="papers found",
            evidence={"paper_count": 3},
        )
        judgement = RetrievalJudgement(
            paper_id="paper_1",
            relevance_score=0.8,
            decision="relevant",
            reason="matches trajectory prediction",
        )
        report = RetrievalEvaluationReport(
            status="pass",
            score=95,
            checks=[check],
            judgements=[judgement],
        )

        self.assertTrue(report.evaluation_id.startswith("retrieval_eval_"))
        self.assertEqual(report.status, "pass")
        self.assertEqual(report.score, 95)
        self.assertEqual(report.checks[0].name, "paper_count")
        self.assertEqual(report.judgements[0].decision, "relevant")
        self.assertEqual(report.summary, [])


def _topic() -> TopicPack:
    return TopicPack(
        topic_name="retrieval_eval_test",
        search_seeds={"keywords": ["trajectory prediction", "diffusion", "pedestrian"]},
    )


def _context(tmp: str, settings: dict | None = None) -> AgentContext:
    return AgentContext(
        artifact_store=ArtifactStore(Path(tmp)),
        memory_store=None,  # type: ignore
        tool_registry=None,  # type: ignore
        settings=settings or {},
    )


class RetrievalEvaluationAgentDeterministicTest(TestCase):
    def test_passes_clean_retrieval_state(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "papers": [
                    {
                        "paper_id": "p1",
                        "title": "Diffusion Models for Pedestrian Trajectory Prediction",
                        "abstract": "Trajectory prediction with diffusion for pedestrians.",
                        "source": "local",
                        "keywords": ["trajectory", "diffusion"],
                    },
                    {
                        "paper_id": "p2",
                        "title": "Language Conditioned Motion Forecasting",
                        "abstract": "Pedestrian motion forecasting.",
                        "source": "reference_seed",
                        "keywords": ["motion", "forecasting"],
                    },
                ],
                "selected_papers": [
                    {
                        "paper_id": "p1",
                        "title": "Diffusion Models for Pedestrian Trajectory Prediction",
                        "abstract": "Trajectory prediction with diffusion for pedestrians.",
                        "source": "local",
                        "keywords": ["trajectory", "diffusion"],
                    },
                ],
                "reference_search_seeds": [
                    {"query": "Language Conditioned Motion Forecasting", "relevance_score": 0.8}
                ],
            })

            result = RetrievalEvaluationAgent().run(state, _context(tmp))

            report = state.values["retrieval_evaluation"]
            self.assertEqual(report["status"], "pass")
            self.assertGreaterEqual(report["score"], 85)
            self.assertIn("retrieval_evaluations", result.artifacts)
            self.assertEqual(state.values["retrieval_evaluation_status"], "pass")

    def test_blocks_when_no_papers(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values["papers"] = []
            state.values["selected_papers"] = []

            RetrievalEvaluationAgent().run(state, _context(tmp))

            report = state.values["retrieval_evaluation"]
            self.assertEqual(report["status"], "block")
            self.assertTrue(any("no candidate papers" in issue for issue in report["blocking_issues"]))

    def test_blocks_when_papers_exist_but_none_selected(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values["papers"] = [{"paper_id": "p1", "title": "Trajectory Prediction", "source": "local"}]
            state.values["selected_papers"] = []

            RetrievalEvaluationAgent().run(state, _context(tmp))

            report = state.values["retrieval_evaluation"]
            self.assertEqual(report["status"], "block")
            self.assertTrue(any("no selected papers" in issue for issue in report["blocking_issues"]))

    def test_warns_when_reference_seeds_not_included(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "papers": [{"paper_id": "p1", "title": "Trajectory Prediction", "source": "local"}],
                "selected_papers": [{"paper_id": "p1", "title": "Trajectory Prediction", "source": "local"}],
                "reference_search_seeds": [{"query": "Language Conditioned Motion", "relevance_score": 0.9}],
            })

            RetrievalEvaluationAgent().run(state, _context(tmp))

            report = state.values["retrieval_evaluation"]
            self.assertEqual(report["status"], "needs_review")
            self.assertTrue(any("reference seeds" in warning for warning in report["warnings"]))

    def test_warns_on_duplicate_title_rate(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "papers": [
                    {"paper_id": "p1", "title": "Same Title", "source": "local"},
                    {"paper_id": "p2", "title": "Same Title", "source": "local"},
                    {"paper_id": "p3", "title": "Different Trajectory Title", "source": "local"},
                ],
                "selected_papers": [{"paper_id": "p3", "title": "Different Trajectory Title", "source": "local"}],
            })

            RetrievalEvaluationAgent().run(state, _context(tmp))

            report = state.values["retrieval_evaluation"]
            duplicate_check = next(c for c in report["checks"] if c["name"] == "duplicate_title_rate")
            self.assertEqual(duplicate_check["status"], "warn")

    def test_warns_on_low_keyword_coverage(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "papers": [{"paper_id": "p1", "title": "Image Classification Survey", "source": "local"}],
                "selected_papers": [{"paper_id": "p1", "title": "Image Classification Survey", "source": "local"}],
            })

            RetrievalEvaluationAgent().run(state, _context(tmp))

            report = state.values["retrieval_evaluation"]
            coverage_check = next(c for c in report["checks"] if c["name"] == "keyword_coverage")
            self.assertEqual(coverage_check["status"], "warn")


class _FakeJudgeClient:
    def __init__(self, response: LLMResponse):
        self.response = response
        self.calls = 0

    def chat(self, route, messages, temperature=0.2, max_tokens=1200, base_url=None):
        self.calls += 1
        return self.response


class RetrievalEvaluationAgentJudgeTest(TestCase):
    def test_judge_not_called_without_both_flags(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "papers": [{"paper_id": "p1", "title": "Trajectory Prediction", "source": "local"}],
                "selected_papers": [{"paper_id": "p1", "title": "Trajectory Prediction", "source": "local"}],
            })
            fake = _FakeJudgeClient(LLMResponse(ok=True, text="{}"))
            agent = RetrievalEvaluationAgent()
            agent.llm_client = fake

            agent.run(state, _context(tmp, {"enable_llm": True, "enable_retrieval_judge": False}))

            self.assertEqual(fake.calls, 0)
            checks = state.values["retrieval_evaluation"]["checks"]
            judge_check = next(c for c in checks if c["name"] == "llm_retrieval_judge")
            self.assertEqual(judge_check["severity"], "info")

    def test_valid_judge_json_adds_judgements(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "papers": [{"paper_id": "p1", "title": "Trajectory Prediction", "source": "local"}],
                "selected_papers": [{"paper_id": "p1", "title": "Trajectory Prediction", "source": "local"}],
            })
            fake = _FakeJudgeClient(LLMResponse(
                ok=True,
                text='{"judgements":[{"paper_id":"p1","relevance_score":0.9,"decision":"relevant","reason":"matches"}]}',
                usage={"total_tokens": 123},
                provider="deepseek",
                model="deepseek-v4-flash",
            ))
            agent = RetrievalEvaluationAgent()
            agent.llm_client = fake

            agent.run(state, _context(tmp, {
                "enable_llm": True,
                "enable_retrieval_judge": True,
                "llm_call_budget": 2,
                "llm_token_budget": 10000,
                "retrieval_judge_top_k": 1,
            }))

            report = state.values["retrieval_evaluation"]
            self.assertEqual(fake.calls, 1)
            self.assertEqual(len(report["judgements"]), 1)
            self.assertEqual(report["judgements"][0]["decision"], "relevant")

    def test_invalid_judge_json_warns_without_crash(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "papers": [{"paper_id": "p1", "title": "Trajectory Prediction", "source": "local"}],
                "selected_papers": [{"paper_id": "p1", "title": "Trajectory Prediction", "source": "local"}],
            })
            fake = _FakeJudgeClient(LLMResponse(ok=True, text="not json", usage={"total_tokens": 10}))
            agent = RetrievalEvaluationAgent()
            agent.llm_client = fake

            agent.run(state, _context(tmp, {
                "enable_llm": True,
                "enable_retrieval_judge": True,
                "llm_call_budget": 2,
                "llm_token_budget": 10000,
            }))

            report = state.values["retrieval_evaluation"]
            self.assertEqual(report["status"], "needs_review")
            self.assertTrue(any("invalid JSON" in warning for warning in report["warnings"]))

    def test_all_irrelevant_judge_blocks(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "papers": [{"paper_id": "p1", "title": "Image Classification", "source": "local"}],
                "selected_papers": [{"paper_id": "p1", "title": "Image Classification", "source": "local"}],
            })
            fake = _FakeJudgeClient(LLMResponse(
                ok=True,
                text='{"judgements":[{"paper_id":"p1","relevance_score":0.1,"decision":"irrelevant","reason":"unrelated"}]}',
                usage={"total_tokens": 20},
            ))
            agent = RetrievalEvaluationAgent()
            agent.llm_client = fake

            agent.run(state, _context(tmp, {
                "enable_llm": True,
                "enable_retrieval_judge": True,
                "llm_call_budget": 2,
                "llm_token_budget": 10000,
            }))

            report = state.values["retrieval_evaluation"]
            self.assertEqual(report["status"], "block")
            self.assertTrue(any("average relevance" in issue for issue in report["blocking_issues"]))


    def test_source_mix_handles_none_source(self):
        """Bug fix: source=None should be counted as 'unknown', not 'None'."""
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "papers": [{"paper_id": "p1", "title": "Test Paper", "source": None}],
                "selected_papers": [{"paper_id": "p1", "title": "Test Paper", "source": None}],
            })

            RetrievalEvaluationAgent().run(state, _context(tmp))

            report = state.values["retrieval_evaluation"]
            source_check = next(c for c in report["checks"] if c["name"] == "source_mix")
            sources = source_check["evidence"]["source_mix"]
            self.assertIn("unknown", sources,
                          f"source=None should be 'unknown', got sources={sources}")
            self.assertNotIn("None", sources)

    def test_non_numeric_relevance_score_does_not_crash(self):
        """Bug fix: non-numeric relevance_score should not crash agent."""
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values.update({
                "papers": [{"paper_id": "p1", "title": "Trajectory Prediction", "source": "local"}],
                "selected_papers": [{"paper_id": "p1", "title": "Trajectory Prediction", "source": "local"}],
                "reference_search_seeds": [
                    {"query": "Diffusion Models", "relevance_score": "bad"},
                    {"query": "Motion Forecasting", "relevance_score": 0.9},
                ],
            })

            RetrievalEvaluationAgent().run(state, _context(tmp))

            report = state.values["retrieval_evaluation"]
            self.assertIn("retrieval_evaluation", state.values)
            seed_check = next(c for c in report["checks"] if c["name"] == "low_relevance_seed_count")
            self.assertEqual(seed_check["evidence"]["low_relevance_seed_count"], 1,
                             "non-numeric 'bad' should be treated as 0.0 (low score)")


class RetrievalEvaluationRouteTest(TestCase):
    def test_missing_retrieval_judge_route_falls_back_to_paper_triage(self):
        """Bug fix: without explicit retrieval_judge route, fallback to paper_triage."""
        from agents.retrieval_evaluator import _retrieval_judge_route

        topic = TopicPack(
            topic_name="no_judge_route",
            metadata={
                "models": {
                    "default": {"provider": "deepseek", "model": "deepseek-v4-pro"},
                    "routes": {
                        "paper_triage": {"provider": "deepseek", "model": "deepseek-v4-flash"},
                    },
                },
            },
        )
        state = ResearchState(topic=topic)
        route = _retrieval_judge_route(state)
        self.assertEqual(route.agent, "paper_triage",
                         f"should fallback to paper_triage, got agent={route.agent} model={route.model}")

    def test_explicit_retrieval_judge_route_used_when_present(self):
        """When retrieval_judge route is explicitly configured, use it."""
        from agents.retrieval_evaluator import _retrieval_judge_route

        topic = TopicPack(
            topic_name="has_judge_route",
            metadata={
                "models": {
                    "default": {"provider": "deepseek", "model": "deepseek-v4-pro"},
                    "routes": {
                        "paper_triage": {"provider": "deepseek", "model": "deepseek-v4-flash"},
                        "retrieval_judge": {"provider": "deepseek", "model": "deepseek-v4-flash"},
                    },
                },
            },
        )
        state = ResearchState(topic=topic)
        route = _retrieval_judge_route(state)
        self.assertEqual(route.agent, "retrieval_judge")

    def test_explicit_offline_retrieval_judge_falls_back_to_paper_triage(self):
        """Explicit retrieval_judge route that is offline should still fallback."""
        from agents.retrieval_evaluator import _retrieval_judge_route

        topic = TopicPack(
            topic_name="offline_judge",
            metadata={
                "models": {
                    "default": {"provider": "deepseek", "model": "deepseek-v4-pro"},
                    "routes": {
                        "paper_triage": {"provider": "deepseek", "model": "deepseek-v4-flash"},
                        "retrieval_judge": {"provider": "offline", "model": "rule_based"},
                    },
                },
            },
        )
        state = ResearchState(topic=topic)
        route = _retrieval_judge_route(state)
        self.assertEqual(route.agent, "paper_triage",
                         "explicit but offline retrieval_judge should fallback to paper_triage")


if __name__ == "__main__":
    main()
