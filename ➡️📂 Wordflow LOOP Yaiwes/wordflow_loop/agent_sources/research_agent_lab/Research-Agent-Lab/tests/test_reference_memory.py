from __future__ import annotations

from tempfile import TemporaryDirectory
from pathlib import Path
from unittest import TestCase, main

from memory.literature_memory import LiteratureMemoryStore


class ReferenceMemoryTest(TestCase):
    def test_write_and_retrieve_references_by_scope(self):
        with TemporaryDirectory() as tmp:
            store = LiteratureMemoryStore(Path(tmp) / "lit.sqlite3")
            store.write_reference({
                "ref_id": "ref_a",
                "title": "Diffusion Models for Pedestrian Trajectory Prediction",
                "source_paper_id": "paper_a",
                "authors": ["A. Researcher"],
                "year": "2024",
                "venue": "CVPR",
                "relevance_score": 0.91,
                "cited_in_sections": ["[1]", "[3]"],
            }, "intent_led_virat")

            refs = store.retrieve_references("intent_led_virat", limit=5)

            self.assertEqual(len(refs), 1)
            self.assertEqual(refs[0]["ref_id"], "ref_a")
            self.assertEqual(refs[0]["title"], "Diffusion Models for Pedestrian Trajectory Prediction")
            self.assertEqual(refs[0]["authors"], ["A. Researcher"])
            self.assertEqual(refs[0]["relevance_score"], 0.91)

    def test_retrieve_references_filters_by_min_score(self):
        with TemporaryDirectory() as tmp:
            store = LiteratureMemoryStore(Path(tmp) / "lit.sqlite3")
            store.write_reference({
                "ref_id": "low",
                "title": "Generic Image Classification",
                "source_paper_id": "paper_a",
                "relevance_score": 0.1,
            }, "scope_a")
            store.write_reference({
                "ref_id": "high",
                "title": "Language Conditioned Motion Forecasting",
                "source_paper_id": "paper_b",
                "relevance_score": 0.8,
            }, "scope_a")

            refs = store.retrieve_references("scope_a", min_score=0.5, limit=10)

            self.assertEqual([r["ref_id"] for r in refs], ["high"])

    def test_write_run_artifacts_persists_extracted_references(self):
        with TemporaryDirectory() as tmp:
            store = LiteratureMemoryStore(Path(tmp) / "lit.sqlite3")
            count = store.write_run_artifacts({
                "extracted_references": [{
                    "ref_id": "ref_run",
                    "title": "Goal Conditioned Trajectory Diffusion",
                    "source_paper_id": "paper_x",
                    "year": "2025",
                    "relevance_score": 0.77,
                }]
            }, "scope_run")

            refs = store.retrieve_references("scope_run", limit=3)

            self.assertEqual(count, 1)
            self.assertEqual(len(refs), 1)
            self.assertEqual(refs[0]["title"], "Goal Conditioned Trajectory Diffusion")


if __name__ == "__main__":
    main()
