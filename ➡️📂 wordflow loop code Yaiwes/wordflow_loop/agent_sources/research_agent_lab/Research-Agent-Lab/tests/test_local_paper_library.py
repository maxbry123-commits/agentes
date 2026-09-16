from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from schemas.topic_pack import TopicPack
from tools.local_paper_library import LocalPaperLibrary
from tools.model_router import ModelRouter


class LocalPaperLibraryTest(unittest.TestCase):
    def test_scan_local_papers(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sub").mkdir()
            (root / "sub" / "Intention-Aware Diffusion Model.pdf").write_text("x", encoding="utf-8")
            topic = TopicPack.from_mapping(
                {
                    "topic_name": "test",
                    "search_seeds": {"keywords": ["intention diffusion trajectory"]},
                    "metadata": {
                        "literature": {
                            "local_paper_dirs": [str(root)],
                            "include_patterns": ["*.pdf"],
                        }
                    },
                }
            )

            papers = LocalPaperLibrary().scan(topic)

            self.assertEqual(len(papers), 1)
            self.assertEqual(papers[0].source, "local_paper")
            self.assertTrue(papers[0].local_path.endswith(".pdf"))

    def test_model_router_defaults_to_offline_without_env(self) -> None:
        topic = TopicPack.from_mapping(
            {
                "topic_name": "test",
                "metadata": {
                    "models": {
                        "default": {"provider": "offline", "model": "rule_based"},
                        "routes": {
                            "reviewer_agent": {
                                "provider": "deepseek",
                                "model": "deepseek-v4-pro",
                                "api_key_env": "DEEPSEEK_API_KEY",
                            }
                        },
                    }
                },
            }
        )

        route = ModelRouter(topic).route_for("reviewer_agent")

        self.assertEqual(route.provider, "deepseek")
        self.assertFalse(route.enabled)

    def test_model_router_carries_task_difficulty(self) -> None:
        topic = TopicPack.from_mapping(
            {
                "topic_name": "test",
                "metadata": {
                    "models": {
                        "default": {"provider": "offline", "model": "rule_based"},
                        "routes": {
                            "paper_triage": {
                                "provider": "deepseek",
                                "model": "deepseek-v4-flash",
                                "api_key_env": "DEEPSEEK_API_KEY",
                                "task_difficulty": "simple",
                            }
                        },
                    }
                },
            }
        )

        route = ModelRouter(topic).route_for("paper_triage")

        self.assertEqual(route.model, "deepseek-v4-flash")
        self.assertEqual(route.task_difficulty, "simple")


if __name__ == "__main__":
    unittest.main()
