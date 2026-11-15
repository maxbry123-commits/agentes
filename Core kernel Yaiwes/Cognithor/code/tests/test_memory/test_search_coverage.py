"""Coverage-Tests fuer search.py -- fehlende Pfade abdecken."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from cognithor.memory.search import HybridSearch, recency_decay

# ============================================================================
# recency_decay
# ============================================================================


class TestRecencyDecay:
    def test_none_date(self) -> None:
        assert recency_decay(None) == 1.0

    def test_today(self) -> None:
        assert recency_decay(date.today()) == 1.0

    def test_future_date(self) -> None:
        future = date.today() + timedelta(days=5)
        assert recency_decay(future) == 1.0

    def test_30_days_ago(self) -> None:
        old = date.today() - timedelta(days=30)
        decay = recency_decay(old, half_life_days=30)
        # 2^(-30/30) = 2^(-1) = 0.5 (true half-life)
        assert 0.49 < decay < 0.51

    def test_datetime_input(self) -> None:
        old = datetime.now() - timedelta(days=30)
        decay = recency_decay(old, half_life_days=30)
        # 2^(-30/30) = 0.5 (true half-life)
        assert 0.49 < decay < 0.51


# ============================================================================
# HybridSearch
# ============================================================================


@pytest.fixture
def mock_index() -> MagicMock:
    idx = MagicMock()
    idx.search_bm25 = MagicMock(return_value=[])
    idx.get_all_embeddings = MagicMock(return_value={})
    idx.get_chunks_by_ids = MagicMock(return_value={})
    idx.search_entities = MagicMock(return_value=[])
    idx.graph_traverse = MagicMock(return_value=[])
    idx.get_chunks_with_entity_overlap = MagicMock(return_value=[])
    idx.conn = MagicMock()
    idx.conn.execute.return_value.fetchall.return_value = []
    return idx


@pytest.fixture
def mock_embeddings() -> MagicMock:
    emb = MagicMock()
    emb.dimensions = 3
    emb.embed_text = AsyncMock()
    return emb


@pytest.fixture
def mock_config() -> MagicMock:
    from cognithor.config import MemoryConfig

    cfg = MemoryConfig()
    return cfg


@pytest.fixture
def hybrid_search(
    mock_index: MagicMock, mock_embeddings: MagicMock, mock_config: MagicMock
) -> HybridSearch:
    return HybridSearch(mock_index, mock_embeddings, mock_config)


class TestHybridSearchProperties:
    def test_index(self, hybrid_search: HybridSearch, mock_index: MagicMock) -> None:
        assert hybrid_search.index is mock_index

    def test_vector_index(self, hybrid_search: HybridSearch) -> None:
        assert hybrid_search.vector_index is not None


class TestNotifyEmbeddingAdded:
    def test_adds_to_vector_index(self, hybrid_search: HybridSearch) -> None:
        hybrid_search.notify_embedding_added("hash1", [1.0, 0.0, 0.0])
        assert hybrid_search._vector_index.size == 1

    def test_incremental_cache_update(self, hybrid_search: HybridSearch) -> None:
        """Inkrementelles Update: Hash-Map wird erweitert statt invalidiert (#44)."""
        hybrid_search._chunk_hash_map = {"a": ["b"]}
        hybrid_search._graph_search_cache["test"] = {}
        hybrid_search.notify_embedding_added("hash1", [1.0, 0.0, 0.0])
        # Hash-Map bleibt erhalten und wird um den neuen Key erweitert
        assert hybrid_search._chunk_hash_map is not None
        assert "a" in hybrid_search._chunk_hash_map
        assert "hash1" in hybrid_search._chunk_hash_map
        # Graph-Cache wird weiterhin invalidiert
        assert len(hybrid_search._graph_search_cache) == 0


class TestInvalidateChunkHashMap:
    def test_clears_both(self, hybrid_search: HybridSearch) -> None:
        hybrid_search._chunk_hash_map = {"a": ["b"]}
        hybrid_search._graph_search_cache["x"] = {}
        hybrid_search.invalidate_chunk_hash_map()
        assert hybrid_search._chunk_hash_map is None
        assert len(hybrid_search._graph_search_cache) == 0


class TestSearch:
    @pytest.mark.asyncio
    async def test_empty_query(self, hybrid_search: HybridSearch) -> None:
        results = await hybrid_search.search("")
        assert results == []

    @pytest.mark.asyncio
    async def test_bm25_only(self, hybrid_search: HybridSearch, mock_index: MagicMock) -> None:
        from cognithor.models import Chunk, MemoryTier

        chunk = Chunk(
            id="c1",
            text="hello",
            source_path="test",
            content_hash="h1",
            memory_tier=MemoryTier.SEMANTIC,
            timestamp=datetime.now(),
        )
        mock_index.search_bm25.return_value = [("c1", 5.0)]
        mock_index.get_chunks_by_ids.return_value = {"c1": chunk}

        results = await hybrid_search.search(
            "hello",
            enable_vector=False,
            enable_graph=False,
        )
        assert len(results) == 1
        assert results[0].bm25_score == 1.0

    @pytest.mark.asyncio
    async def test_core_no_decay(self, hybrid_search: HybridSearch, mock_index: MagicMock) -> None:
        from cognithor.models import Chunk, MemoryTier

        chunk = Chunk(
            id="c1",
            text="core",
            source_path="CORE.md",
            content_hash="h1",
            memory_tier=MemoryTier.CORE,
            timestamp=datetime.now() - timedelta(days=365),
        )
        mock_index.search_bm25.return_value = [("c1", 1.0)]
        mock_index.get_chunks_by_ids.return_value = {"c1": chunk}

        results = await hybrid_search.search(
            "core",
            enable_vector=False,
            enable_graph=False,
        )
        assert len(results) == 1
        assert results[0].recency_factor == 1.0


class TestSearchBm25Only:
    def test_empty(self, hybrid_search: HybridSearch, mock_index: MagicMock) -> None:
        mock_index.search_bm25.return_value = []
        results = hybrid_search.search_bm25_only("test")
        assert results == []

    def test_with_results(self, hybrid_search: HybridSearch, mock_index: MagicMock) -> None:
        from cognithor.models import Chunk, MemoryTier

        chunk = Chunk(
            id="c1",
            text="hello",
            source_path="test",
            content_hash="h1",
            memory_tier=MemoryTier.SEMANTIC,
            timestamp=datetime.now(),
        )
        mock_index.search_bm25.return_value = [("c1", 3.0)]
        mock_index.get_chunks_by_ids.return_value = {"c1": chunk}

        results = hybrid_search.search_bm25_only("hello")
        assert len(results) == 1
        assert results[0].bm25_score == 1.0

    def test_missing_chunk(self, hybrid_search: HybridSearch, mock_index: MagicMock) -> None:
        mock_index.search_bm25.return_value = [("c1", 3.0)]
        mock_index.get_chunks_by_ids.return_value = {}
        results = hybrid_search.search_bm25_only("hello")
        assert results == []


class TestGraphSearch:
    def test_no_entities(self, hybrid_search: HybridSearch, mock_index: MagicMock) -> None:
        mock_index.search_entities.return_value = []
        result = hybrid_search._graph_search("test")
        assert result == {}

    def test_cached(self, hybrid_search: HybridSearch) -> None:
        cache_key = frozenset(["test"])
        hybrid_search._graph_search_cache[cache_key] = {"c1": 0.5}
        result = hybrid_search._graph_search("test")
        assert result == {"c1": 0.5}

    def test_with_entities(self, hybrid_search: HybridSearch, mock_index: MagicMock) -> None:
        entity = MagicMock()
        entity.id = "e1"
        mock_index.search_entities.return_value = [entity]
        mock_index.graph_traverse.return_value = []
        mock_index.get_chunks_with_entity_overlap.return_value = [
            ("c1", ["e1"]),
        ]
        result = hybrid_search._graph_search("test")
        assert "c1" in result
        assert result["c1"] > 0

    def test_cache_eviction(self, hybrid_search: HybridSearch, mock_index: MagicMock) -> None:
        hybrid_search._GRAPH_CACHE_MAX_SIZE = 2
        # The eviction code only runs for non-empty entity results (line 426-428).
        # Empty-entity results return early at line 399 without eviction.
        # So we need entities to trigger eviction.
        entity = MagicMock()
        entity.id = "e1"
        mock_index.search_entities.return_value = [entity]
        mock_index.graph_traverse.return_value = []
        mock_index.get_chunks_with_entity_overlap.return_value = []
        hybrid_search._graph_search("query1")
        hybrid_search._graph_search("query2")
        hybrid_search._graph_search("query3")
        assert len(hybrid_search._graph_search_cache) <= 2
