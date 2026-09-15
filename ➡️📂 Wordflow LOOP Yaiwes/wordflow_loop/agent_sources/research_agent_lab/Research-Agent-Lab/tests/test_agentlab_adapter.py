from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from schemas.topic_pack import load_topic_pack
from tools.agent_laboratory_adapter import AgentLaboratoryAdapter
from tools.project_safety import ProjectSafetyPolicy


class AgentLaboratoryAdapterTest(unittest.TestCase):
    def test_agentlab_config_generation(self) -> None:
        topic = load_topic_pack(Path("topics/intent_led_virat.json"))
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "AgentLaboratory"
            repo.mkdir()
            (repo / "ai_lab_repo.py").write_text("# stub", encoding="utf-8")
            output = Path(tmp) / "config.yaml"

            config = AgentLaboratoryAdapter(repo).write_config(topic, output)

            self.assertTrue(output.exists())
            text = output.read_text(encoding="utf-8")
            self.assertIn("copilot-mode: True", text)
            self.assertIn("intent_conditioned_led_virat", text)
            self.assertIn("--yaml-location", config.command)

    def test_project_safety_policy_flags_paths(self) -> None:
        topic = load_topic_pack(Path("topics/intent_led_virat.json"))
        policy = ProjectSafetyPolicy.from_topic(topic)

        self.assertTrue(policy.is_allowed("models/model_diffusion.py"))
        self.assertTrue(policy.is_protected("results/checkpoints/model.p"))
        self.assertIn(
            "protected path cannot be edited: results/checkpoints/model.p",
            policy.validate_planned_paths(["results/checkpoints/model.p"]),
        )


if __name__ == "__main__":
    unittest.main()
