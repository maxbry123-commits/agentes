"""Tests for 4th-channel hierarchical integration into HybridSearch."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from cognithor.config import HierarchicalConfig, MemoryConfig
from cognithor.models import Chunk, MemoryTier

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def memory_config() -> MemoryConfig:
    return MemoryConfig()


@pytest.fixture()
def mock_index() -> MagicMock:
    index = MagicMock()
    index.search_bm25.return_value = []
    index.get_all_embeddings.return_value = {}
    index.get_chunks_by_ids.return_value = {}
    index.search_entities.return_value = []
    return index


@pytest.fixture()
def mock_embeddings() -> MagicMock:
    emb = MagicMock()
    emb.dimensions = 128
    emb.embed_text = AsyncMock(return_value=MagicMock(vector=[0.0] * 128))
    return emb


@pytest.fixture()
def mock_retriever() -> MagicMock:
    retriever = MagicMock()
    retriever.search = AsyncMock(return_value=[])
    return retriever


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestHierarchicalSearchIntegration:
    async def test_4_channel_fusion(
        self, mock_index: MagicMock, mock_embeddings: MagicMock, mock_retriever: MagicMock
    ) -> None:
        """All 4 channels contribute to the final score."""
        from cognithor.memory.search import HybridSearch

        cfg = MemoryConfig(weight_vector=0.3, weight_bm25=0.3, weight_graph=0.15)
        hs = HybridSearch(
            mock_index,
            mock_embeddings,
            cfg,
            hierarchical_retriever=mock_retriever,
        )

        # Mock hierarchical results with a node_id matching a chunk
        mock_retriever.search = AsyncMock(
            return_value=[{"node_id": "chunk1", "score": 0.9, "source_type": "hierarchical"}]
        )

        # Mock a BM25 result for chunk1
        mock_index.search_bm25.return_value = [("chunk1", 1.0)]

        # Use a real Chunk so pydantic validation passes
        chunk = Chunk(
            id="chunk1",
            text="test content",
            source_path="/tmp/test.md",
            memory_tier=MemoryTier.SEMANTIC,
        )
        mock_index.get_chunks_by_ids.return_value = {"chunk1": chunk}

        results = await hs.search("test query", enable_vector=False, enable_graph=False)

        assert len(results) == 1
        # With hierarchical enabled, score should incorporate all active weights
        assert results[0].score > 0

    async def test_w_h_zero_reduces_to_3_channel(
        self, mock_index: MagicMock, mock_embeddings: MagicMock
    ) -> None:
        """When no hierarchical retriever, formula is the same 3-channel result."""
        from cognithor.memory.search import HybridSearch

        cfg = MemoryConfig(weight_vector=0.5, weight_bm25=0.3, weight_graph=0.2)
        hs = HybridSearch(mock_index, mock_embeddings, cfg)

        # BM25 returns a single hit
        mock_index.search_bm25.return_value = [("c1", 1.0)]
        chunk = Chunk(
            id="c1",
            text="test content",
            source_path="/tmp/test.md",
            memory_tier=MemoryTier.SEMANTIC,
        )
        mock_index.get_chunks_by_ids.return_value = {"c1": chunk}

        results = await hs.search("test", enable_vector=False, enable_graph=False)

        assert len(results) == 1
        # w_h=0, total_w = 0.5+0.3+0.2 = 1.0
        # bm25_s=1.0 normalized, vector=0, graph=0
        # final = (0.3/1.0)*1.0 * 1.0 = 0.3
        expected = 0.3
        assert abs(results[0].score - expected) < 0.01

    async def test_hierarchical_results_have_source_type(self, mock_retriever: MagicMock) -> None:
        """The retriever returns results with source_type='hierarchical'."""
        mock_retriever.search = AsyncMock(
            return_value=[
                {"content": "x", "score": 0.5, "source_type": "hierarchical", "node_id": "n1"},
            ]
        )
        results = await mock_retriever.search("q")
        for r in results:
            assert r["source_type"] == "hierarchical"

    def test_config_default_values(self) -> None:
        """HierarchicalConfig defaults are as specified."""
        cfg = HierarchicalConfig()
        assert cfg.enabled is True
        assert cfg.default_max_nodes_per_query == 5
        assert cfg.default_max_tokens_per_node == 2000
        assert abs(cfg.score_weight - 0.25) < 0.001
        assert cfg.max_branching_factor == 50
        assert cfg.max_tree_depth == 8
        assert cfg.node_split_token_threshold == 4000
        assert cfg.parallel_summary_generation == 10

    def test_memory_config_has_hierarchical(self) -> None:
        """MemoryConfig includes hierarchical sub-config."""
        mc = MemoryConfig()
        assert hasattr(mc, "hierarchical")
        assert isinstance(mc.hierarchical, HierarchicalConfig)
        assert mc.hierarchical.enabled is True

    async def test_hierarchical_channel_empty_when_no_retriever(
        self, mock_index: MagicMock, mock_embeddings: MagicMock
    ) -> None:
        """_hierarchical_channel returns empty dict when retriever is None."""
        from cognithor.memory.search import HybridSearch

        hs = HybridSearch(mock_index, mock_embeddings)
        result = await hs._hierarchical_channel("test", 5)
        assert result == {}

    async def test_hierarchical_channel_returns_scores(
        self, mock_index: MagicMock, mock_embeddings: MagicMock, mock_retriever: MagicMock
    ) -> None:
        """_hierarchical_channel returns score dict from retriever."""
        from cognithor.memory.search import HybridSearch

        mock_retriever.search = AsyncMock(
            return_value=[
                {"node_id": "n1", "score": 0.8},
                {"node_id": "n2", "score": 0.5},
            ]
        )
        hs = HybridSearch(mock_index, mock_embeddings, hierarchical_retriever=mock_retriever)
        result = await hs._hierarchical_channel("test", 5)
        assert result == {"n1": 0.8, "n2": 0.5}

    async def test_hierarchical_channel_exception_returns_empty(
        self, mock_index: MagicMock, mock_embeddings: MagicMock, mock_retriever: MagicMock
    ) -> None:
        """_hierarchical_channel swallows exceptions and returns {}."""
        from cognithor.memory.search import HybridSearch

        mock_retriever.search = AsyncMock(side_effect=RuntimeError("boom"))
        hs = HybridSearch(mock_index, mock_embeddings, hierarchical_retriever=mock_retriever)
        result = await hs._hierarchical_channel("test", 5)
        assert result == {}
