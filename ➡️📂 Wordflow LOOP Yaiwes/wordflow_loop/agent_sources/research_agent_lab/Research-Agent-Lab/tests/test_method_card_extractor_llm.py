from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from agents.method_card_extractor import MethodCardExtractorAgent
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState
from memory.sqlite_memory import SQLiteMemoryStore
from schemas.topic_pack import TopicPack
from tools.llm_client import LLMResponse
from tools.tool_registry import build_default_tool_registry


class FakeLLMClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def chat(self, route, messages, temperature: float = 0.2, max_tokens: int = 1200, base_url=None):
        self.calls.append(
            {
                "route": route,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "base_url": base_url,
            }
        )
        return LLMResponse(
            ok=True,
            text=json.dumps(
                {
                    "task": "intention-conditioned trajectory prediction",
                    "problem_setting": "predict future pedestrian trajectories from motion and intent cues",
                    "input_modalities": ["trajectory", "intent"],
                    "output": "future trajectory",
                    "model_architecture": {"encoder": "trajectory encoder", "decoder": "diffusion decoder"},
                    "temporal_modeling": "history-to-future sequence modeling",
                    "fusion_strategy": {"type": "conditioning", "description": "intent feature conditioning"},
                    "training_objective": "trajectory reconstruction loss",
                    "datasets": ["VIRAT"],
                    "metrics": ["ADE", "FDE"],
                    "main_results": "excerpt does not provide numeric results",
                    "limitations": ["requires full paper verification"],
                    "reusable_ideas_for_current_topic": ["inject intent features into LED initializer"],
                    "implementation_difficulty": "medium",
                    "risk": ["paper excerpt may be incomplete"],
                }
            ),
            provider=route.provider,
            model=route.model,
            usage={"total_tokens": 123},
        )


def make_topic() -> TopicPack:
    return TopicPack.from_mapping(
        {
            "topic_name": "intent_led_test",
            "domain": {"primary_area": "pedestrian_trajectory_prediction"},
            "research_goal": {"short": "test intent-conditioned trajectory prediction"},
            "current_status": {"datasets": ["VIRAT"]},
            "paper_schema": {
                "default_input_modalities": ["trajectory", "intention"],
                "default_output": "future trajectory",
            },
            "experiment_metrics": ["ADE", "FDE"],
            "metadata": {
                "models": {
                    "default": {"provider": "offline", "model": "rule_based"},
                    "routes": {
                        "method_card_extractor": {
                            "provider": "deepseek",
                            "model": "deepseek-v4-pro",
                            "api_key_env": "DEEPSEEK_API_KEY",
                            "task_difficulty": "hard",
                        }
                    },
                }
            },
        }
    )


class MethodCardExtractorLLMTest(unittest.TestCase):
    def test_method_card_extractor_uses_llm_route_when_enabled(self) -> None:
        old_key = os.environ.get("DEEPSEEK_API_KEY")
        os.environ["DEEPSEEK_API_KEY"] = "sk-test-key-for-route-enable"
        try:
            topic = make_topic()
            state = ResearchState(topic=topic)
            state.values["selected_papers"] = [
                {"paper_id": "paper_1", "title": "Intent conditioned LED", "source": "local_paper"}
            ]
            state.values["parsed_papers"] = [
                {
                    "paper_id": "paper_1",
                    "text_excerpt": "This method conditions trajectory diffusion on pedestrian intent cues.",
                }
            ]
            state.values["checked_evidence"] = [
                {"paper_id": "paper_1", "evidence_id": "ev_1", "is_usable": True}
            ]

            with TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                context = AgentContext(
                    artifact_store=ArtifactStore(tmp_path / "runs"),
                    memory_store=SQLiteMemoryStore(tmp_path / "memory.sqlite3"),
                    tool_registry=build_default_tool_registry(),
                    settings={"enable_llm": True},
                )
                fake = FakeLLMClient()
                result = MethodCardExtractorAgent(llm_client=fake).run(state, context)

                self.assertEqual(len(fake.calls), 1)
                self.assertEqual(fake.calls[0]["route"].model, "deepseek-v4-pro")
                self.assertEqual(result.values["method_card_llm_success_count"], 1)
                self.assertEqual(state.values["method_cards"][0]["training_objective"], "trajectory reconstruction loss")
                self.assertTrue((tmp_path / "runs" / state.run_id / "artifacts" / "llm_calls").exists())
        finally:
            if old_key is None:
                os.environ.pop("DEEPSEEK_API_KEY", None)
            else:
                os.environ["DEEPSEEK_API_KEY"] = old_key

    def test_method_card_extractor_stays_offline_by_default(self) -> None:
        topic = make_topic()
        state = ResearchState(topic=topic)
        state.values["selected_papers"] = [
            {"paper_id": "paper_1", "title": "Intent conditioned LED", "source": "local_paper"}
        ]
        state.values["parsed_papers"] = [
            {
                "paper_id": "paper_1",
                "text_excerpt": "This method conditions trajectory diffusion on pedestrian intent cues.",
            }
        ]

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            context = AgentContext(
                artifact_store=ArtifactStore(tmp_path / "runs"),
                memory_store=SQLiteMemoryStore(tmp_path / "memory.sqlite3"),
                tool_registry=build_default_tool_registry(),
                settings={"enable_llm": False},
            )
            fake = FakeLLMClient()
            result = MethodCardExtractorAgent(llm_client=fake).run(state, context)

            self.assertEqual(fake.calls, [])
            self.assertEqual(result.values["method_card_llm_call_count"], 0)

    def test_method_card_extractor_respects_call_budget(self) -> None:
        old_key = os.environ.get("DEEPSEEK_API_KEY")
        os.environ["DEEPSEEK_API_KEY"] = "sk-test-key-for-route-enable"
        try:
            topic = make_topic()
            state = ResearchState(topic=topic)
            state.values["selected_papers"] = [
                {"paper_id": "paper_1", "title": "Intent conditioned LED", "source": "local_paper"}
            ]
            state.values["parsed_papers"] = [
                {
                    "paper_id": "paper_1",
                    "text_excerpt": "This method conditions trajectory diffusion on pedestrian intent cues.",
                }
            ]

            with TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                context = AgentContext(
                    artifact_store=ArtifactStore(tmp_path / "runs"),
                    memory_store=SQLiteMemoryStore(tmp_path / "memory.sqlite3"),
                    tool_registry=build_default_tool_registry(),
                    settings={"enable_llm": True, "llm_call_budget": 0, "llm_token_budget": 20000},
                )
                fake = FakeLLMClient()
                result = MethodCardExtractorAgent(llm_client=fake).run(state, context)

                self.assertEqual(fake.calls, [])
                self.assertEqual(result.values["method_card_llm_call_count"], 0)
                self.assertEqual(result.values["method_card_llm_record_count"], 1)
                self.assertEqual(result.values["method_card_llm_success_count"], 0)
                call_log = next((tmp_path / "runs" / state.run_id / "artifacts" / "llm_calls").glob("*.json"))
                self.assertEqual(json.loads(call_log.read_text(encoding="utf-8"))["status"], "skipped_call_budget")
        finally:
            if old_key is None:
                os.environ.pop("DEEPSEEK_API_KEY", None)
            else:
                os.environ["DEEPSEEK_API_KEY"] = old_key


if __name__ == "__main__":
    unittest.main()
