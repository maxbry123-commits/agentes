from __future__ import annotations

import unittest

from schemas.topic_pack import TopicPack
from tools.paper_chunk_selector import PaperChunkSelector


class PaperChunkSelectorTest(unittest.TestCase):
    def test_selector_prefers_method_related_chunks(self) -> None:
        topic = TopicPack.from_mapping(
            {
                "topic_name": "intent_led_test",
                "domain": {"primary_area": "pedestrian_trajectory_prediction"},
                "search_seeds": {"keywords": ["diffusion trajectory prediction", "intention"]},
                "experiment_metrics": ["ADE", "FDE"],
            }
        )
        paper = {"paper_id": "paper_1", "title": "Diffusion intention trajectory forecasting"}
        parsed = {
            "chunks": [
                {
                    "paper_id": "paper_1",
                    "chunk_id": "chunk_intro",
                    "section": "Introduction",
                    "text": "This paper discusses related work and motivation.",
                },
                {
                    "paper_id": "paper_1",
                    "chunk_id": "chunk_method",
                    "section": "Method",
                    "text": "Our method uses a diffusion decoder with intention fusion for trajectory prediction.",
                },
            ]
        }

        selected = PaperChunkSelector(max_chunks=1).select_for_paper(topic, paper, parsed)

        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0].chunk_id, "chunk_method")
        self.assertIn("diffusion", selected[0].matched_terms)


if __name__ == "__main__":
    unittest.main()
