from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from schemas.topic_pack import TopicPack
from tools.codebase_analyzer import CodebaseAnalyzer


class CodebaseAnalyzerTest(unittest.TestCase):
    def test_analyzer_extracts_integration_points(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "models").mkdir()
            (root / "trainer").mkdir()
            (root / "data").mkdir()
            (root / "cfg" / "virat").mkdir(parents=True)
            (root / "work.md").write_text("# notes", encoding="utf-8")
            (root / "models" / "model_led_initializer.py").write_text(
                "class LEDInitializer:\n    def forward(self):\n        pass\n",
                encoding="utf-8",
            )
            (root / "trainer" / "train_led_trajectory_augment_input.py").write_text(
                "def data_preprocess(data):\n    return data['pre_motion_3D']\n",
                encoding="utf-8",
            )
            (root / "data" / "dataloader_virat.py").write_text(
                "class VIRATDataset:\n    pass\n",
                encoding="utf-8",
            )
            (root / "cfg" / "virat" / "led_virat_debug.yml").write_text(
                "dataset: virat\nnum_agents: 2\n",
                encoding="utf-8",
            )
            topic = TopicPack.from_mapping(
                {
                    "topic_name": "test",
                    "codebase": {
                        "repo_path": str(root),
                        "allowed_auto_edit": ["models/*", "trainer/*", "data/*", "cfg/virat/*"],
                    },
                }
            )

            report = CodebaseAnalyzer().analyze(topic)
            dumped = json.dumps(report.suggested_first_patch_files)

            self.assertIn("trainer/train_led_trajectory_augment_input.py", dumped)
            self.assertTrue(report.integration_points)


class CodebaseAnalyzerExperimentTagTest(unittest.TestCase):
    def test_experiment_tag_from_topic_pack(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "work.md").write_text("# test", encoding="utf-8")
            topic = TopicPack.from_mapping({
                "topic_name": "test",
                "codebase": {
                    "repo_path": str(root),
                    "experiment_tag": "custom_tag",
                    "allowed_auto_edit": [],
                },
            })
            report = CodebaseAnalyzer().analyze(topic)
            self.assertEqual(len(report.smoke_commands), 2)
            self.assertIn("--info custom_tag", report.smoke_commands[0])
            self.assertIn("--info custom_tag", report.smoke_commands[1])

    def test_experiment_tag_default_when_absent(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "work.md").write_text("# test", encoding="utf-8")
            topic = TopicPack.from_mapping({
                "topic_name": "test",
                "codebase": {
                    "repo_path": str(root),
                    "allowed_auto_edit": [],
                },
            })
            report = CodebaseAnalyzer().analyze(topic)
            self.assertIn("--info motion_condition", report.smoke_commands[0])


if __name__ == "__main__":
    unittest.main()
