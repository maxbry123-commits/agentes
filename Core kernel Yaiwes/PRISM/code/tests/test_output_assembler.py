"""Tests for Phase 4: output assembly."""

from mmem.config import RetrievalConfig
from mmem.core.edges import make_belongs_to
from mmem.core.graph import MemoryGraph
from mmem.core.nodes import Episode, Facet, FacetPoint
from mmem.retrieval.output_assembler import RetrievalResult, assemble_output
from mmem.retrieval.path_scorer import EpisodeBundle


def _build_graph_and_bundles():
    g = MemoryGraph()
    ep1 = g.add_node(Episode(summary="Alice joined Acme in 2020"))
    ep2 = g.add_node(Episode(summary="Alice left Acme in 2024"))
    fa = g.add_node(Facet(theme="career"))
    fp = g.add_node(FacetPoint(content="she worked as an engineer"))

    g.add_edge(make_belongs_to(fp.id, fa.id))
    g.add_edge(make_belongs_to(fa.id, ep1.id))
    g.add_edge(make_belongs_to(fa.id, ep2.id))

    bundles = [
        EpisodeBundle(episode_id=ep1.id, score=0.2, best_path="point"),
        EpisodeBundle(episode_id=ep2.id, score=0.5, best_path="facet"),
    ]
    return g, bundles, ep1, ep2, fa, fp


class TestTopK:
    def test_selects_top_k(self):
        g, bundles, ep1, ep2, fa, fp = _build_graph_and_bundles()
        result = assemble_output(bundles, g, top_k=1)
        assert len(result.bundles) == 1
        assert result.bundles[0].episode_id == ep1.id

    def test_respects_score_order(self):
        g, bundles, ep1, ep2, fa, fp = _build_graph_and_bundles()
        result = assemble_output(bundles, g, top_k=2)
        assert result.bundles[0].score <= result.bundles[1].score


class TestSummaryMode:
    def test_summary_contains_episode_summaries(self):
        g, bundles, ep1, ep2, fa, fp = _build_graph_and_bundles()
        result = assemble_output(bundles, g, display_mode="summary")
        assert "Alice joined Acme" in result.context_text
        assert "Alice left Acme" in result.context_text

    def test_summary_numbered(self):
        g, bundles, ep1, ep2, fa, fp = _build_graph_and_bundles()
        result = assemble_output(bundles, g, display_mode="summary")
        assert "[1]" in result.context_text
        assert "[2]" in result.context_text


class TestDetailMode:
    def test_detail_includes_facet_and_fp(self):
        g, bundles, ep1, ep2, fa, fp = _build_graph_and_bundles()
        result = assemble_output(bundles, g, display_mode="detail")
        assert "career" in result.context_text
        assert "engineer" in result.context_text

    def test_detail_includes_summary(self):
        g, bundles, ep1, ep2, fa, fp = _build_graph_and_bundles()
        result = assemble_output(bundles, g, display_mode="detail")
        assert "Alice joined Acme" in result.context_text


class TestDebugInfo:
    def test_debug_info_populated(self):
        g, bundles, ep1, ep2, fa, fp = _build_graph_and_bundles()
        result = assemble_output(bundles, g)
        assert result.debug_info["total_candidates"] == 2
        assert "top_k" in result.debug_info
        assert "display_mode" in result.debug_info
