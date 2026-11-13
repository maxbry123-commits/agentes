from __future__ import annotations

from unittest import TestCase, main

from tools.literature_retriever import LiteratureRetriever


class LiteratureRetrieverTest(TestCase):
    def setUp(self):
        self.papers = [
            {"paper_id": "paper_1", "title": "Diffusion for Trajectory Prediction"},
            {"paper_id": "paper_2", "title": "Language Conditioned Forecasting"},
        ]
        self.parsed = [
            {
                "paper_id": "paper_1",
                "text_excerpt": "",
                "chunks": [
                    {"chunk_id": "c1", "section": "Abstract", "text": "We use diffusion models for pedestrian trajectory prediction on VIRAT."},
                    {"chunk_id": "c2", "section": "Method", "text": "The denoising network takes trajectory history and outputs future positions. We use cross-attention for intent conditioning."},
                    {"chunk_id": "c3", "section": "Experiments", "text": "Our model achieves ADE 0.30 and FDE 0.55 on the VIRAT benchmark."},
                ],
            },
            {
                "paper_id": "paper_2",
                "text_excerpt": "",
                "chunks": [
                    {"chunk_id": "d1", "section": "Abstract", "text": "We condition trajectory prediction on natural language descriptions."},
                    {"chunk_id": "d2", "section": "Method", "text": "Text embeddings are fused via gated attention into the trajectory decoder."},
                ],
            },
        ]

    def test_index_and_search(self):
        r = LiteratureRetriever()
        n = r.index(self.papers, self.parsed)
        self.assertEqual(n, 5)

        results = r.search("diffusion trajectory prediction")
        self.assertGreater(len(results), 0)
        top = results[0]
        self.assertIn("diffusion", top.matched_terms)

    def test_prefer_method_sections(self):
        r = LiteratureRetriever()
        r.index(self.papers, self.parsed)
        results = r.search("trajectory prediction", top_k=5, prefer_sections=["Method"])
        self.assertGreater(len(results), 0)
        # Method section should rank high
        method_found = any("Method" in res.section for res in results[:3])
        self.assertTrue(method_found)

    def test_empty_index(self):
        r = LiteratureRetriever()
        results = r.search("anything")
        self.assertEqual(results, [])

    def test_no_match_returns_empty(self):
        r = LiteratureRetriever()
        r.index(self.papers, self.parsed)
        results = r.search("zzz_nonexistent_xyzzy")
        self.assertEqual(results, [])

    def test_matched_terms_recorded(self):
        r = LiteratureRetriever()
        r.index(self.papers, self.parsed)
        results = r.search("diffusion VIRAT")
        for res in results:
            if res.paper_id == "paper_1":
                terms = [t.lower() for t in res.matched_terms]
                self.assertTrue(any("diffusion" in t for t in terms) or any("virat" in t for t in terms))

    def test_prefer_sections_bonus(self):
        r = LiteratureRetriever()
        r.index(self.papers, self.parsed)
        results = r.search("trajectory", prefer_sections=["Method", "Experiments"])
        if len(results) >= 2:
            method_sections = [r for r in results if r.section in ("Method", "Experiments")]
            self.assertGreater(len(method_sections), 0)


if __name__ == "__main__":
    main()
