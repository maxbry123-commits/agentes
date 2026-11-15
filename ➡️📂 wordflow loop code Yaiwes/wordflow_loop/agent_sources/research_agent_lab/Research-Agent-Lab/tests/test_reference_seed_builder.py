from __future__ import annotations

from unittest import TestCase, main

from tools.reference_seed_builder import build_reference_search_seeds


class ReferenceSeedBuilderTest(TestCase):
    def test_builds_seed_from_high_score_reference_title(self):
        refs = [{
            "title": "Language Conditioned Pedestrian Trajectory Forecasting",
            "relevance_score": 0.88,
            "year": "2024",
        }]

        seeds = build_reference_search_seeds(refs, topic_keywords=["trajectory", "language"], max_seeds=5)

        self.assertEqual(seeds[0]["query"], "Language Conditioned Pedestrian Trajectory Forecasting")
        self.assertEqual(seeds[0]["source"], "reference_network")
        self.assertEqual(seeds[0]["relevance_score"], 0.88)

    def test_filters_low_score_and_short_titles(self):
        refs = [
            {"title": "AI", "relevance_score": 0.9},
            {"title": "Unrelated Classification Survey", "relevance_score": 0.1},
            {"title": "Diffusion Trajectory Prediction", "relevance_score": 0.7},
        ]

        seeds = build_reference_search_seeds(refs, topic_keywords=["trajectory"], min_score=0.3, max_seeds=5)

        self.assertEqual([s["query"] for s in seeds], ["Diffusion Trajectory Prediction"])

    def test_deduplicates_similar_titles(self):
        refs = [
            {"title": "Diffusion Models for Trajectory Prediction", "relevance_score": 0.9},
            {"title": "Diffusion Model for Trajectory Prediction", "relevance_score": 0.8},
            {"title": "Graph Neural Forecasting", "relevance_score": 0.7},
        ]

        seeds = build_reference_search_seeds(refs, topic_keywords=["trajectory"], max_seeds=5)

        self.assertEqual(len(seeds), 2)
        self.assertEqual(seeds[0]["query"], "Diffusion Models for Trajectory Prediction")

    def test_respects_max_seeds(self):
        refs = [
            {"title": f"Relevant Trajectory Paper {i}", "relevance_score": 1.0 - i * 0.01}
            for i in range(10)
        ]

        seeds = build_reference_search_seeds(refs, topic_keywords=["trajectory"], max_seeds=3)

        self.assertEqual(len(seeds), 3)


if __name__ == "__main__":
    main()
