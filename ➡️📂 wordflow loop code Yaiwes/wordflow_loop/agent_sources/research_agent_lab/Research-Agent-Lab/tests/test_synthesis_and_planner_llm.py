from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from agents.experiment_planner import ExperimentPlannerAgent
from agents.synthesis_agent import SynthesisAgent
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState
from memory.sqlite_memory import SQLiteMemoryStore
from schemas.topic_pack import TopicPack
from tools.llm_client import LLMResponse
from tools.tool_registry import build_default_tool_registry


class RoutingFakeLLMClient:
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
        if route.agent == "synthesis":
            return LLMResponse(
                ok=True,
                text=json.dumps(
                    {
                        "report_markdown": "# Synthesis\n\nEvidence-backed method theme.",
                        "evidence_warnings": ["One claim is pending verification."],
                    }
                ),
                provider=route.provider,
                model=route.model,
                usage={"total_tokens": 50},
            )
        return LLMResponse(
            ok=True,
            text=json.dumps(
                {
                    "name": "Intent feature ablation",
                    "hypothesis": "Motion-derived intent features improve FDE.",
                    "baseline": "LED VIRAT baseline",
                    "modification": "Add a gated intent feature to the initializer.",
                    "files_to_change": ["models/model_led_initializer.py", "trainer/train_led_trajectory_augment_input.py"],
                    "dataset": "VIRAT",
                    "training_config": {
                        "mode": "smoke-first",
                        "smoke_test_command": "python main_led_nba.py --cfg cfg/virat/led_virat_intent_debug.yml --train 1",
                    },
                    "metrics": ["ADE", "FDE"],
                    "ablation_studies": ["baseline unchanged", "intent feature disabled"],
                    "acceptance_criteria": {"must_run": True, "no_data_leakage": True},
                    "rollback_plan": "Restore backed-up initializer and trainer files.",
                }
            ),
            provider=route.provider,
            model=route.model,
            usage={"total_tokens": 70},
        )


def make_topic() -> TopicPack:
    return TopicPack.from_mapping(
        {
            "topic_name": "intent_led_test",
            "domain": {"primary_area": "pedestrian_trajectory_prediction"},
            "research_goal": {"short": "test intent conditioning"},
            "current_status": {
                "dataset": "VIRAT",
                "baseline_methods": ["LED VIRAT baseline"],
            },
            "experiment_metrics": ["ADE", "FDE"],
            "codebase": {
                "allowed_auto_edit": [
                    "models/*",
                    "trainer/*",
                    "cfg/virat/*",
                    "work.md",
                ]
            },
            "metadata": {
                "models": {
                    "default": {"provider": "offline", "model": "rule_based"},
                    "routes": {
                        "synthesis": {
                            "provider": "deepseek",
                            "model": "deepseek-v4-flash",
                            "api_key_env": "DEEPSEEK_API_KEY",
                            "task_difficulty": "simple",
                        },
                        "experiment_planner": {
                            "provider": "deepseek",
                            "model": "deepseek-v4-pro",
                            "api_key_env": "DEEPSEEK_API_KEY",
                            "task_difficulty": "hard",
                        },
                    },
                }
            },
        }
    )


def make_context(tmp_path: Path, enable_llm: bool = True, budget: int = 5) -> AgentContext:
    return AgentContext(
        artifact_store=ArtifactStore(tmp_path / "runs"),
        memory_store=SQLiteMemoryStore(tmp_path / "memory.sqlite3"),
        tool_registry=build_default_tool_registry(),
        settings={"enable_llm": enable_llm, "llm_call_budget": budget, "llm_token_budget": 10000},
    )


class SynthesisAndPlannerLLMTest(unittest.TestCase):
    def setUp(self) -> None:
        self.old_key = os.environ.get("DEEPSEEK_API_KEY")
        os.environ["DEEPSEEK_API_KEY"] = "sk-test-key-for-route-enable"

    def tearDown(self) -> None:
        if self.old_key is None:
            os.environ.pop("DEEPSEEK_API_KEY", None)
        else:
            os.environ["DEEPSEEK_API_KEY"] = self.old_key

    def test_synthesis_uses_flash_route_when_enabled(self) -> None:
        state = ResearchState(topic=make_topic())
        state.values["method_cards"] = [
            {
                "paper_id": "paper_1",
                "task": "trajectory prediction",
                "input_modalities": ["trajectory", "intent"],
                "evidence_ids": ["ev_1"],
            }
        ]
        state.values["checked_evidence"] = [{"evidence_id": "ev_1", "is_usable": True}]

        with TemporaryDirectory() as tmp:
            fake = RoutingFakeLLMClient()
            result = SynthesisAgent(llm_client=fake).run(state, make_context(Path(tmp)))

            self.assertEqual(len(fake.calls), 1)
            self.assertEqual(fake.calls[0]["route"].model, "deepseek-v4-flash")
            self.assertIn("Evidence-backed", state.values["synthesis_report"])
            self.assertEqual(result.values["synthesis_llm_success_count"], 1)

    def test_experiment_planner_uses_pro_route_when_enabled(self) -> None:
        state = ResearchState(topic=make_topic())
        state.values["method_cards"] = [{"paper_id": "paper_1", "task": "trajectory prediction"}]
        state.values["synthesis_report"] = "# Synthesis\nEvidence-backed method theme."
        state.values["opportunities"] = [
            {
                "title": "Intent feature ablation",
                "hypothesis": "Intent helps prediction.",
                "technical_strategy": "Add gated intent feature.",
            }
        ]
        state.values["codebase_report"] = {
            "suggested_first_patch_files": [
                "models/model_led_initializer.py",
                "trainer/train_led_trajectory_augment_input.py",
            ]
        }

        with TemporaryDirectory() as tmp:
            fake = RoutingFakeLLMClient()
            result = ExperimentPlannerAgent(llm_client=fake).run(state, make_context(Path(tmp)))

            self.assertEqual(len(fake.calls), 1)
            self.assertEqual(fake.calls[0]["route"].model, "deepseek-v4-pro")
            self.assertEqual(result.values["experiment_planner_llm_success_count"], 1)
            self.assertIn("smoke_test_command", state.values["experiment_plans"][0]["training_config"])

    def test_experiment_planner_respects_call_budget(self) -> None:
        state = ResearchState(topic=make_topic())
        state.values["opportunities"] = [{"title": "Budgeted plan", "hypothesis": "Budget test."}]

        with TemporaryDirectory() as tmp:
            fake = RoutingFakeLLMClient()
            result = ExperimentPlannerAgent(llm_client=fake).run(
                state,
                make_context(Path(tmp), budget=0),
            )

            self.assertEqual(fake.calls, [])
            self.assertEqual(result.values["experiment_planner_llm_success_count"], 0)
            self.assertEqual(state.values["experiment_planner_llm_call_count"], 0)


class ExperimentPlannerCommandsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.old_key = os.environ.get("DEEPSEEK_API_KEY")
        os.environ["DEEPSEEK_API_KEY"] = "sk-test-key-for-route-enable"

    def tearDown(self) -> None:
        if self.old_key is None:
            os.environ.pop("DEEPSEEK_API_KEY", None)
        else:
            os.environ["DEEPSEEK_API_KEY"] = self.old_key

    def test_plan_from_payload_extracts_commands(self):
        agent = ExperimentPlannerAgent()
        state = ResearchState(topic=make_topic())
        state.values["opportunities"] = [{"title": "test", "hypothesis": "test", "technical_strategy": "test"}]
        state.values["codebase_report"] = {"suggested_first_patch_files": []}
        base_plan = agent._rule_based_plan(state)
        payload = {
            "name": "test",
            "hypothesis": "test",
            "files_to_change": [],
            "commands": ["python train.py --train 1 --max_epochs 10"],
        }
        plan = agent._plan_from_payload(state, payload, base_plan)
        self.assertEqual(plan.commands, ["python train.py --train 1 --max_epochs 10"])

    def test_plan_from_payload_commands_default_to_empty(self):
        agent = ExperimentPlannerAgent()
        state = ResearchState(topic=make_topic())
        state.values["opportunities"] = [{"title": "test", "hypothesis": "test", "technical_strategy": "test"}]
        state.values["codebase_report"] = {"suggested_first_patch_files": []}
        base_plan = agent._rule_based_plan(state)
        payload = {"name": "test", "hypothesis": "test", "files_to_change": []}
        plan = agent._plan_from_payload(state, payload, base_plan)
        self.assertEqual(plan.commands, [])


if __name__ == "__main__":
    unittest.main()
