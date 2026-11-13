from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from agents.literature_searcher import LiteratureSearchAgent
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState
from memory.literature_memory import LiteratureMemoryStore
from schemas.topic_pack import TopicPack
from tools.arxiv_tool import ArxivTool
from tools.tool_registry import ToolRegistry


def _topic() -> TopicPack:
    return TopicPack(
        topic_name="intent_led_virat",
        search_seeds={"keywords": ["trajectory prediction", "language condition"]},
    )


class ReferenceExpansionSearchTest(TestCase):
    def test_reference_expansion_adds_offline_reference_seed_papers(self):
        with TemporaryDirectory() as tmp:
            lit_store = LiteratureMemoryStore(Path(tmp) / "lit.sqlite3")
            lit_store.write_reference(
                {
                    "ref_id": "ref_1",
                    "title": "Language Conditioned Trajectory Diffusion",
                    "source_paper_id": "paper_a",
                    "relevance_score": 0.9,
                },
                "intent_led_virat",
            )
            state = ResearchState(topic=_topic())
            ctx = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None,
                tool_registry=None,
                settings={
                    "max_papers": 3,
                    "enable_reference_expansion": True,
                    "max_reference_seeds": 2,
                },
            )

            result = LiteratureSearchAgent(lit_memory_store=lit_store).run(state, ctx)

            papers = state.values["papers"]
            titles = [p["title"] for p in papers]
            self.assertTrue(
                any(
                    "Language Conditioned Trajectory Diffusion" in title
                    for title in titles
                )
            )
            self.assertIn("reference_search_seeds", result.artifacts)

    def test_reference_seeds_not_truncated_by_local_papers(self):
        """Regression: when local_papers fill max_papers, reference seeds must still appear."""
        with TemporaryDirectory() as tmp:
            lit_store = LiteratureMemoryStore(Path(tmp) / "lit.sqlite3")
            lit_store.write_reference(
                {
                    "ref_id": "ref_1",
                    "title": "Must Appear Reference Paper",
                    "source_paper_id": "paper_a",
                    "relevance_score": 0.9,
                },
                "intent_led_virat",
            )
            state = ResearchState(topic=_topic())
            # Simulate 47 local papers filling the library
            state.values["local_papers"] = [
                {"paper_id": f"local_{i}", "title": f"Local Paper {i}",
                 "abstract": "", "keywords": [], "source": "local_paper"}
                for i in range(47)
            ]
            ctx = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None,
                tool_registry=None,
                settings={
                    "max_papers": 3,
                    "enable_reference_expansion": True,
                    "max_reference_seeds": 2,
                },
            )

            LiteratureSearchAgent(lit_memory_store=lit_store).run(state, ctx)

            papers = state.values["papers"]
            sources = [p.get("source", "") for p in papers]
            self.assertTrue(
                any("reference_seed" in s for s in sources),
                f"Reference seed paper must be present when enable_reference_expansion=True, "
                f"got sources={sources}",
            )
            # 1 local + 1 reference seed = 2 (only 1 ref in DB to expand from)
            self.assertGreaterEqual(len(papers), 2,
                                    f"Should have at least 2 papers, got {len(papers)}")

    def test_reference_expansion_disabled_keeps_default_offline_keywords(self):
        with TemporaryDirectory() as tmp:
            lit_store = LiteratureMemoryStore(Path(tmp) / "lit.sqlite3")
            lit_store.write_reference(
                {
                    "ref_id": "ref_1",
                    "title": "Reference Expansion Should Not Appear",
                    "relevance_score": 0.9,
                },
                "intent_led_virat",
            )
            state = ResearchState(topic=_topic())
            ctx = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None,
                tool_registry=None,
                settings={"max_papers": 2, "enable_reference_expansion": False},
            )

            LiteratureSearchAgent(lit_memory_store=lit_store).run(state, ctx)

            titles = [p["title"] for p in state.values["papers"]]
            self.assertFalse(
                any(
                    "Reference Expansion Should Not Appear" in title
                    for title in titles
                )
            )

    def test_reference_seeds_online_path_does_not_require_settings_online_key(self):
        """Reference seed arXiv path works when tool_registry has arxiv, regardless of settings."""
        with TemporaryDirectory() as tmp:
            lit_store = LiteratureMemoryStore(Path(tmp) / "lit.sqlite3")
            lit_store.write_reference(
                {
                    "ref_id": "ref_online",
                    "title": "Online Reference Paper",
                    "source_paper_id": "paper_online",
                    "relevance_score": 0.95,
                },
                "intent_led_virat",
            )
            state = ResearchState(topic=_topic())
            tools = ToolRegistry()
            tools.register(ArxivTool(max_results=3))

            ctx = AgentContext(
                artifact_store=ArtifactStore(Path(tmp)),
                memory_store=None,
                tool_registry=tools,
                settings={
                    "max_papers": 3,
                    "enable_reference_expansion": True,
                    "max_reference_seeds": 1,
                },
            )

            result = LiteratureSearchAgent(lit_memory_store=lit_store).run(state, ctx)

            papers = state.values["papers"]
            self.assertGreaterEqual(len(papers), 1)


if __name__ == "__main__":
    main()
