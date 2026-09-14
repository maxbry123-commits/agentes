"""Tests for the causal consolidation module."""

from __future__ import annotations

import numpy as np
import pytest

from mmem.config import MMemConfig, WriteConfig
from mmem.core.edges import EdgeType, make_causal
from mmem.core.graph import MemoryGraph
from mmem.core.nodes import Entity, Episode, NodeType
from mmem.indexing.vector_store import VectorStore
from mmem.ingestion.consolidation import run_consolidation
from mmem.ingestion.extractor import CausalPair

DIM = 8


# ── Fakes ─────────────────────────────────────────────────────────────


class FakeEmbedder:
    @property
    def dimension(self) -> int:
        return DIM

    def embed(self, text: str) -> np.ndarray:
        rng = np.random.RandomState(hash(text) % (2**31))
        vec = rng.randn(DIM).astype(np.float32)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        return np.stack([self.embed(t) for t in texts])


class FakeExtractorForCausal:
    """Returns a fixed list of CausalPairs from extract_causal."""

    def __init__(self, pairs: list[CausalPair]) -> None:
        self._pairs = pairs
        self.call_count = 0

    def extract_causal(self, episodes) -> list[CausalPair]:
        self.call_count += 1
        return list(self._pairs)


class ExplodingExtractor:
    """Always raises from extract_causal."""

    def extract_causal(self, episodes):
        raise RuntimeError("LLM is down")


# ── Helpers ───────────────────────────────────────────────────────────


def _make_graph_with_episodes(n: int) -> tuple[MemoryGraph, list[Episode]]:
    g = MemoryGraph()
    episodes = []
    for i in range(n):
        ep = Episode(summary=f"Episode {i}")
        g.add_node(ep)
        episodes.append(ep)
    return g, episodes


def _make_deps(
    n_episodes: int = 3,
    pairs: list[CausalPair] | None = None,
    config: MMemConfig | None = None,
):
    graph, episodes = _make_graph_with_episodes(n_episodes)
    vs = VectorStore(dimension=DIM)
    embedder = FakeEmbedder()
    cfg = config or MMemConfig()

    default_pairs = pairs if pairs is not None else [
        CausalPair(
            cause_id=episodes[0].id,
            effect_id=episodes[1].id,
            description="Ep0 caused Ep1",
            confidence=0.9,
        ),
    ]
    extractor = FakeExtractorForCausal(default_pairs)

    return graph, vs, extractor, embedder, cfg, episodes


# ═══════════════════════════════════════════════════════════════════════
# Basic flow
# ═══════════════════════════════════════════════════════════════════════


class TestBasicFlow:
    def test_creates_causal_edge(self):
        graph, vs, ext, emb, cfg, eps = _make_deps()
        ids = run_consolidation(graph, vs, ext, emb, cfg)

        assert len(ids) == 1
        edge = graph.get_edge(ids[0])
        assert edge is not None
        assert edge.edge_type == EdgeType.CAUSAL
        assert edge.source_id == eps[0].id
        assert edge.target_id == eps[1].id

    def test_returns_new_edge_ids(self):
        graph, vs, ext, emb, cfg, eps = _make_deps()
        ids = run_consolidation(graph, vs, ext, emb, cfg)
        assert len(ids) == 1
        assert all(isinstance(i, str) for i in ids)

    def test_vectorizes_causal_edges(self):
        graph, vs, ext, emb, cfg, eps = _make_deps()
        assert vs.count("edge_relation") == 0

        run_consolidation(graph, vs, ext, emb, cfg)
        assert vs.count("edge_relation") == 1

    def test_multiple_pairs(self):
        graph, vs, ext, emb, cfg, eps = _make_deps(
            n_episodes=4,
            pairs=None,
        )
        ext = FakeExtractorForCausal([
            CausalPair(
                cause_id=eps[0].id, effect_id=eps[1].id,
                description="0→1", confidence=0.9,
            ),
            CausalPair(
                cause_id=eps[2].id, effect_id=eps[3].id,
                description="2→3", confidence=0.85,
            ),
        ])
        ids = run_consolidation(graph, vs, ext, emb, cfg)
        assert len(ids) == 2

    def test_calls_extract_causal(self):
        graph, vs, ext, emb, cfg, eps = _make_deps()
        run_consolidation(graph, vs, ext, emb, cfg)
        assert ext.call_count == 1


# ═══════════════════════════════════════════════════════════════════════
# Confidence filtering
# ═══════════════════════════════════════════════════════════════════════


class TestConfidenceFilter:
    def test_low_confidence_filtered(self):
        graph, vs, _, emb, cfg, eps = _make_deps()
        ext = FakeExtractorForCausal([
            CausalPair(
                cause_id=eps[0].id, effect_id=eps[1].id,
                description="weak", confidence=0.5,
            ),
        ])
        ids = run_consolidation(graph, vs, ext, emb, cfg)
        assert len(ids) == 0

    def test_mixed_confidence(self):
        graph, vs, _, emb, cfg, eps = _make_deps(n_episodes=3)
        ext = FakeExtractorForCausal([
            CausalPair(
                cause_id=eps[0].id, effect_id=eps[1].id,
                description="strong", confidence=0.9,
            ),
            CausalPair(
                cause_id=eps[1].id, effect_id=eps[2].id,
                description="weak", confidence=0.3,
            ),
        ])
        ids = run_consolidation(graph, vs, ext, emb, cfg)
        assert len(ids) == 1

    def test_custom_threshold(self):
        cfg = MMemConfig(write=WriteConfig(causal_confidence_threshold=0.95))
        graph, vs, _, emb, _, eps = _make_deps(config=cfg)
        ext = FakeExtractorForCausal([
            CausalPair(
                cause_id=eps[0].id, effect_id=eps[1].id,
                description="d", confidence=0.9,
            ),
        ])
        ids = run_consolidation(graph, vs, ext, emb, cfg)
        assert len(ids) == 0


# ═══════════════════════════════════════════════════════════════════════
# Duplicate edge check
# ═══════════════════════════════════════════════════════════════════════


class TestDuplicateEdge:
    def test_skips_existing_causal_edge(self):
        graph, vs, ext, emb, cfg, eps = _make_deps()

        existing = make_causal(eps[0].id, eps[1].id, "already exists", confidence=0.8)
        graph.add_edge(existing)

        ids = run_consolidation(graph, vs, ext, emb, cfg)
        assert len(ids) == 0

        causal_edges = graph.get_edges_by_type(EdgeType.CAUSAL)
        assert len(causal_edges) == 1

    def test_allows_reverse_direction(self):
        graph, vs, _, emb, cfg, eps = _make_deps()

        existing = make_causal(eps[1].id, eps[0].id, "reverse", confidence=0.8)
        graph.add_edge(existing)

        ext = FakeExtractorForCausal([
            CausalPair(
                cause_id=eps[0].id, effect_id=eps[1].id,
                description="forward", confidence=0.9,
            ),
        ])
        ids = run_consolidation(graph, vs, ext, emb, cfg)
        assert len(ids) == 1


# ═══════════════════════════════════════════════════════════════════════
# Invalid IDs
# ═══════════════════════════════════════════════════════════════════════


class TestInvalidIDs:
    def test_nonexistent_cause_id_skipped(self):
        graph, vs, _, emb, cfg, eps = _make_deps()
        ext = FakeExtractorForCausal([
            CausalPair(
                cause_id="nonexistent",
                effect_id=eps[1].id,
                description="bad", confidence=0.9,
            ),
        ])
        ids = run_consolidation(graph, vs, ext, emb, cfg)
        assert len(ids) == 0

    def test_nonexistent_effect_id_skipped(self):
        graph, vs, _, emb, cfg, eps = _make_deps()
        ext = FakeExtractorForCausal([
            CausalPair(
                cause_id=eps[0].id,
                effect_id="nonexistent",
                description="bad", confidence=0.9,
            ),
        ])
        ids = run_consolidation(graph, vs, ext, emb, cfg)
        assert len(ids) == 0

    def test_valid_and_invalid_mixed(self):
        graph, vs, _, emb, cfg, eps = _make_deps()
        ext = FakeExtractorForCausal([
            CausalPair(
                cause_id=eps[0].id, effect_id=eps[1].id,
                description="good", confidence=0.9,
            ),
            CausalPair(
                cause_id="ghost", effect_id=eps[2].id,
                description="bad", confidence=0.9,
            ),
        ])
        ids = run_consolidation(graph, vs, ext, emb, cfg)
        assert len(ids) == 1


# ═══════════════════════════════════════════════════════════════════════
# LLM failure
# ═══════════════════════════════════════════════════════════════════════


class TestLLMFailure:
    def test_exception_returns_empty(self):
        graph, vs, _, emb, cfg, eps = _make_deps()
        ext = ExplodingExtractor()
        ids = run_consolidation(graph, vs, ext, emb, cfg)
        assert ids == []

    def test_exception_does_not_modify_graph(self):
        graph, vs, _, emb, cfg, eps = _make_deps()
        edges_before = graph.num_edges
        ext = ExplodingExtractor()
        run_consolidation(graph, vs, ext, emb, cfg)
        assert graph.num_edges == edges_before


# ═══════════════════════════════════════════════════════════════════════
# Edge cases
# ═══════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_fewer_than_two_episodes_returns_empty(self):
        graph, vs, ext, emb, cfg, eps = _make_deps(n_episodes=1, pairs=[])
        ids = run_consolidation(graph, vs, ext, emb, cfg)
        assert ids == []

    def test_empty_graph_returns_empty(self):
        graph = MemoryGraph()
        vs = VectorStore(dimension=DIM)
        ext = FakeExtractorForCausal([])
        emb = FakeEmbedder()
        ids = run_consolidation(graph, vs, ext, emb)
        assert ids == []

    def test_extract_returns_empty_list(self):
        graph, vs, _, emb, cfg, eps = _make_deps()
        ext = FakeExtractorForCausal([])
        ids = run_consolidation(graph, vs, ext, emb, cfg)
        assert ids == []

    def test_recent_episodes_respects_interval(self):
        cfg = MMemConfig(write=WriteConfig(causal_consolidation_interval=2))
        graph, vs, _, emb, _, eps = _make_deps(n_episodes=5, config=cfg)
        ext = FakeExtractorForCausal([
            CausalPair(
                cause_id=eps[3].id, effect_id=eps[4].id,
                description="d", confidence=0.9,
            ),
        ])
        ids = run_consolidation(graph, vs, ext, emb, cfg)
        assert len(ids) == 1
        assert ext.call_count == 1
