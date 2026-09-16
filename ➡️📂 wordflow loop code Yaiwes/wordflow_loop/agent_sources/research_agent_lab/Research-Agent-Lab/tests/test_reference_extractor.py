from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from agents.reference_extractor import (
    ReferenceExtractorAgent,
    _count_citations,
    _deduplicate,
    _extract_title_from_author_year,
    _find_reference_section,
    _parse_reference_entries,
    _rule_based_extract,
    _tf_idf_similarity,
    _top_cited_sections,
    _topic_keywords,
)
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState
from schemas.reference import ExtractedReference
from schemas.topic_pack import TopicPack


def _topic() -> TopicPack:
    return TopicPack(
        topic_name="ref_test",
        search_seeds={"keywords": ["trajectory prediction", "diffusion", "transformer"]},
    )


def _context(tmp: str, settings: dict | None = None) -> AgentContext:
    return AgentContext(
        artifact_store=ArtifactStore(Path(tmp)),
        memory_store=None,  # type: ignore
        tool_registry=None,  # type: ignore
        settings=settings or {},
    )


class ReferenceExtractHelpersTest(TestCase):
    def test_find_reference_section(self):
        chunks = [
            {"section": "Introduction", "text": "Some intro text."},
            {"section": "Method", "text": "Method description."},
            {"section": "References", "text": "[1] Paper A. In CVPR 2023."},
            {"section": "references", "text": "[2] Paper B. In NeurIPS 2022."},
        ]
        ref_text = _find_reference_section(chunks)
        self.assertIn("Paper A", ref_text)
        self.assertIn("Paper B", ref_text)

    def test_find_reference_section_empty(self):
        chunks = [
            {"section": "Introduction", "text": "Intro."},
            {"section": "Method", "text": "Method."},
        ]
        ref_text = _find_reference_section(chunks)
        self.assertEqual(ref_text, "")

    def test_find_reference_section_bibliography(self):
        chunks = [
            {"section": "Bibliography", "text": "[1] Some paper."},
        ]
        ref_text = _find_reference_section(chunks)
        self.assertIn("Some paper", ref_text)

    def test_count_citations(self):
        chunks = [
            {"section": "Introduction", "text": "Prior work [1] [2] has shown."},
            {"section": "Related Work", "text": "Methods [1] [3] [3] are relevant."},
            {"section": "Method", "text": "We extend [2] [4]."},
            {"section": "Experiments", "text": "Results are shown in Table 1."},
        ]
        counts = _count_citations(chunks)
        self.assertEqual(counts["1"], 2)
        self.assertEqual(counts["2"], 2)
        self.assertEqual(counts["3"], 2)
        self.assertEqual(counts["4"], 1)
        self.assertNotIn("Table", counts)

    def test_count_citations_empty(self):
        counts = _count_citations([])
        self.assertEqual(len(counts), 0)

    def test_parse_reference_entries_standard(self):
        text = (
            "[1] A. Smith, \"Trajectory Prediction with Diffusion Models\", In CVPR 2023.\n"
            "[2] B. Jones, \"Transformer-Based Forecasting\", In NeurIPS 2022.\n"
            "[3,4] C. Lee, \"Multi-Agent Motion\".\n"
        )
        entries = _parse_reference_entries(text)
        self.assertEqual(len(entries), 3)
        titles = [e["title"] for e in entries]
        self.assertIn("Trajectory Prediction with Diffusion Models", titles)
        self.assertIn("Transformer-Based Forecasting", titles)

    def test_parse_reference_entries_multi_number(self):
        text = "[1,2,3] Authors, \"Paper Title\", Venue 2023."
        entries = _parse_reference_entries(text)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["numbers"], [1, 2, 3])

    def test_tf_idf_similarity(self):
        score = _tf_idf_similarity(
            "Trajectory Prediction with Diffusion Models",
            ["trajectory", "prediction", "diffusion"],
        )
        self.assertGreater(score, 0.5)

    def test_tf_idf_similarity_no_match(self):
        score = _tf_idf_similarity(
            "Image Classification with CNNs",
            ["trajectory", "prediction", "diffusion"],
        )
        self.assertEqual(score, 0.0)

    def test_tf_idf_similarity_empty(self):
        self.assertEqual(_tf_idf_similarity("", []), 0.0)
        self.assertEqual(_tf_idf_similarity("Title", []), 0.0)

    def test_rule_based_extract_scoring(self):
        text = (
            "[1] A. Smith, \"Trajectory Prediction with Diffusion Models\", In CVPR 2023.\n"
            "[2] B. Jones, \"Image Classification\", In ICCV 2022.\n"
        )
        from collections import Counter
        cited = Counter({"1": 3, "2": 1})
        refs = _rule_based_extract("paper_x", text, cited, ["trajectory", "prediction", "diffusion"])
        self.assertGreaterEqual(len(refs), 1)
        self.assertTrue(all(0.0 <= r.relevance_score <= 1.0 for r in refs))

    def test_dedup_removes_similar_titles(self):
        refs = [
            ExtractedReference(title="Trajectory Prediction with Diffusion Models", source_paper_id="a"),
            ExtractedReference(title="Trajectory Prediction using Diffusion Models", source_paper_id="b"),
            ExtractedReference(title="Image Classification", source_paper_id="c"),
        ]
        deduped = _deduplicate(refs, max_total=20)
        self.assertEqual(len(deduped), 2)

    def test_dedup_respects_max_total(self):
        distinct_titles = [
            "Deep Learning for Trajectory Prediction",
            "Graph Neural Networks Survey",
            "Attention Mechanisms in NLP",
            "Reinforcement Learning Basics",
            "Computer Vision Applications",
            "Natural Language Generation",
            "Speech Recognition Systems",
            "Recommendation Engine Design",
            "Distributed Computing Patterns",
            "Database Optimization Methods",
            "Operating System Principles",
            "Network Security Protocols",
            "Compiler Design Theory",
            "Machine Learning Operations",
            "Data Mining Techniques",
            "Software Engineering Practices",
            "Cloud Computing Architecture",
            "Edge Computing Frameworks",
            "Quantum Computing Introduction",
            "Blockchain Consensus Algorithms",
            "Robotics Motion Planning",
            "Autonomous Vehicle Systems",
            "Biomedical Image Analysis",
            "Climate Modeling Approaches",
            "Financial Forecasting Models",
            "Game Theory Applications",
            "Information Retrieval Systems",
            "Knowledge Graph Construction",
            "Parallel Programming Models",
            "Statistical Learning Theory",
        ]
        refs = [
            ExtractedReference(title=t, source_paper_id="p")
            for t in distinct_titles
        ]
        deduped = _deduplicate(refs, max_total=10)
        self.assertEqual(len(deduped), 10)

    def test_topic_keywords(self):
        state = ResearchState(topic=_topic())
        kw = _topic_keywords(state)
        self.assertIn("trajectory prediction", kw)
        self.assertIn("diffusion", kw)

    def test_top_cited_sections_matches_title_to_ref_number(self):
        """Bug 2 regression: _top_cited_sections should look up the actual citation number for a given title."""
        from collections import Counter

        ref_text = (
            '[1] A. Smith, "Trajectory Prediction with Diffusion Models", In CVPR 2023.\n'
            '[3] B. Jones, "Image Classification with CNNs", In ICCV 2022.\n'
        )
        cited = Counter({"1": 5, "3": 3, "7": 2})

        result1 = _top_cited_sections("Trajectory Prediction with Diffusion Models", ref_text, cited)
        self.assertEqual(result1, ["[1]"],
                         f"Should match title to [1], got {result1}")

        result3 = _top_cited_sections("Image Classification with CNNs", ref_text, cited)
        self.assertEqual(result3, ["[3]"],
                         f"Should match title to [3], got {result3}")

    def test_top_cited_sections_fallback_when_title_not_in_ref_text(self):
        """Bug 2 regression: fall back to most-common citations when title not found."""
        from collections import Counter

        ref_text = '[1] A. Smith, "Some Paper", In CVPR 2023.'
        cited = Counter({"1": 5, "2": 3})

        result = _top_cited_sections("Nonexistent Title", ref_text, cited)
        self.assertEqual(result, ["[1]", "[2]"],
                         f"Should fall back to top cited, got {result}")

    def test_extract_title_year_at_end_format(self):
        """Regression: Authors. Title. Venue, Year. should extract title, not authors."""
        # Format: year at END — title between authors and venue
        text = (
            "Alahi, A.; Goel, K.; Ramanathan, V.; Robicquet, A.; "
            "Fei-Fei, L.; and Savarese, S. Social LSTM: Human trajectory "
            "prediction in crowded spaces. In Proceedings of the IEEE/CVF "
            "Conference on Computer Vision and Pattern Recognition, 2016."
        )
        title = _extract_title_from_author_year(text, "2016")
        self.assertIn("Social LSTM", title,
                      f"Should extract title, got: {title}")
        self.assertNotIn("Alahi", title,
                         f"Title should not contain author name: {title}")

    def test_extract_title_year_in_middle_format(self):
        """Year appears before title — extract what follows the year."""
        text = (
            "Alahi, A.; Goel, K.; Ramanathan, V.; Fei-Fei, L.; "
            "and Savarese, S. 2016. Social LSTM: Human trajectory "
            "prediction in crowded spaces. In Proceedings of CVPR."
        )
        title = _extract_title_from_author_year(text, "2016")
        self.assertIn("Social LSTM", title,
                      f"Should extract title after year, got: {title}")
        self.assertNotIn("Alahi", title,
                         f"Title should not contain author name: {title}")


class ReferenceExtractAgentTest(TestCase):
    def test_extracts_rule_based_from_parsed_papers(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            chunks = [
                {"section": "Introduction", "text": "We cite [1] [2] in this work."},
                {"section": "Method", "text": "Our method builds on [1]."},
                {"section": "References",
                 "text": '[1] A. Smith, "Trajectory Prediction with Diffusion Models", In CVPR 2023.\n'
                         '[2] B. Jones, "Image Classification", In ICCV 2022.'},
            ]
            state.values["parsed_papers"] = [
                {"paper_id": "paper_a", "chunks": chunks},
            ]

            result = ReferenceExtractorAgent().run(state, _context(tmp, {"enable_llm": False}))

            refs = state.values.get("extracted_references", [])
            self.assertGreaterEqual(len(refs), 1)
            self.assertIn("extracted_references", result.artifacts)
            self.assertIn("extracted_reference_count", result.values)

    def test_skips_paper_without_references_section(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            state.values["parsed_papers"] = [
                {"paper_id": "paper_b", "chunks": [
                    {"section": "Introduction", "text": "Some intro."},
                    {"section": "Method", "text": "Some method."},
                ]},
            ]

            result = ReferenceExtractorAgent().run(state, _context(tmp, {"enable_llm": False}))

            refs = state.values.get("extracted_references", [])
            self.assertEqual(len(refs), 0)
            self.assertIn("extracted 0 references", result.notes[0])

    def test_llm_path_with_valid_route(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=TopicPack(
                topic_name="llm_test",
                search_seeds={"keywords": ["trajectory", "prediction"]},
                metadata={"models": {
                    "routes": {
                        "paper_triage": {
                            "provider": "deepseek",
                            "model": "deepseek-v4-flash",
                            "api_key_env": "DEEPSEEK_API_KEY",
                        }
                    }
                }},
            ))
            chunks = [
                {"section": "Introduction", "text": "We cite [1]."},
                {"section": "References",
                 "text": '[1] A. Smith, "Trajectory Prediction", In CVPR 2023.'},
            ]
            state.values["parsed_papers"] = [
                {"paper_id": "paper_c", "chunks": chunks},
            ]

            ctx = _context(tmp, {
                "enable_llm": True,
                "llm_call_budget": 10,
                "llm_token_budget": 50000,
            })

            agent = ReferenceExtractorAgent()
            result = agent.run(state, ctx)

            refs = state.values.get("extracted_references", [])
            # LLM path may fail (no API key) — falls back to rule-based, so we should still get refs
            self.assertGreaterEqual(len(refs), 1)

    def test_llm_path_no_budget_falls_back(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=TopicPack(
                topic_name="budget_test",
                search_seeds={"keywords": ["trajectory"]},
                metadata={"models": {
                    "routes": {
                        "paper_triage": {
                            "provider": "deepseek",
                            "model": "deepseek-v4-flash",
                            "api_key_env": "DEEPSEEK_API_KEY",
                        }
                    }
                }},
            ))
            state.values["parsed_papers"] = [
                {"paper_id": "paper_d", "chunks": [
                    {"section": "References",
                     "text": '[1] Author, "Paper Title", In Venue 2023.'},
                ]},
            ]
            state.values["llm_calls_used"] = 10

            ctx = _context(tmp, {
                "enable_llm": True,
                "llm_call_budget": 5,
                "llm_token_budget": 50000,
            })

            result = ReferenceExtractorAgent().run(state, ctx)
            refs = state.values.get("extracted_references", [])
            self.assertGreaterEqual(len(refs), 1)

    def test_dedup_across_multiple_papers(self):
        with TemporaryDirectory() as tmp:
            state = ResearchState(topic=_topic())
            ref_text = '[1] A. Smith, "Trajectory Prediction with Diffusion Models", In CVPR 2023.'
            state.values["parsed_papers"] = [
                {"paper_id": "paper_e", "chunks": [
                    {"section": "References", "text": ref_text},
                ]},
                {"paper_id": "paper_f", "chunks": [
                    {"section": "References", "text": ref_text},
                ]},
            ]

            result = ReferenceExtractorAgent().run(state, _context(tmp, {"enable_llm": False}))
            refs = state.values.get("extracted_references", [])
            self.assertEqual(len(refs), 1)

    def test_extract_authors_and_year_from_text(self):
        text = (
            '[1] Smith, Jones, "Trajectory Prediction with Diffusion Models", In CVPR (2023).\n'
            '[2] Lee; Kim, "Transformer Forecasting", In NeurIPS 2022.\n'
        )
        entries = _parse_reference_entries(text)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["year"], "2023")
        self.assertEqual(entries[1]["year"], "2022")
        self.assertGreater(len(entries[0]["authors"]), 0)


if __name__ == "__main__":
    main()
