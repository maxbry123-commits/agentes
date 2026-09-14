"""Coverage-Tests fuer embeddings.py -- fehlende Pfade abdecken."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cognithor.memory.embeddings import (
    EmbeddingClient,
    EmbeddingResult,
    EmbeddingStats,
    GeminiEmbeddingProvider,
    NullEmbeddingProvider,
    OllamaEmbeddingProvider,
    OpenAICompatibleEmbeddingProvider,
    cosine_similarity,
    create_embedding_provider,
)

# ============================================================================
# EmbeddingResult / EmbeddingStats
# ============================================================================


class TestEmbeddingResult:
    def test_defaults(self) -> None:
        r = EmbeddingResult(vector=[1.0, 2.0], model="test", dimensions=2)
        assert r.cached is False

    def test_cached(self) -> None:
        r = EmbeddingResult(vector=[1.0], model="test", dimensions=1, cached=True)
        assert r.cached is True


class TestEmbeddingStats:
    def test_defaults(self) -> None:
        s = EmbeddingStats()
        assert s.total_requests == 0
        assert s.cache_hit_rate == 0.0

    def test_cache_hit_rate(self) -> None:
        s = EmbeddingStats(total_requests=10, cache_hits=3)
        assert abs(s.cache_hit_rate - 0.3) < 1e-5


# ============================================================================
# cosine_similarity
# ============================================================================


class TestCosineSimilarity:
    def test_identical(self) -> None:
        assert abs(cosine_similarity([1.0, 0.0], [1.0, 0.0]) - 1.0) < 1e-5

    def test_orthogonal(self) -> None:
        assert abs(cosine_similarity([1.0, 0.0], [0.0, 1.0])) < 1e-5

    def test_opposite(self) -> None:
        assert abs(cosine_similarity([1.0, 0.0], [-1.0, 0.0]) + 1.0) < 1e-5

    def test_different_lengths(self) -> None:
        assert cosine_similarity([1.0], [1.0, 2.0]) == 0.0

    def test_zero_vectors(self) -> None:
        assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0


# ============================================================================
# NullEmbeddingProvider
# ============================================================================


class TestNullEmbeddingProvider:
    @pytest.mark.asyncio
    async def test_embed_single_raises(self) -> None:
        p = NullEmbeddingProvider(backend_name="anthropic")
        with pytest.raises(NotImplementedError, match="anthropic"):
            await p.embed_single("model", "text")

    @pytest.mark.asyncio
    async def test_embed_batch_raises(self) -> None:
        p = NullEmbeddingProvider(backend_name="groq")
        with pytest.raises(NotImplementedError, match="groq"):
            await p.embed_batch_raw("model", ["text1", "text2"])


# ============================================================================
# OllamaEmbeddingProvider
# ============================================================================


class TestOllamaEmbeddingProvider:
    @pytest.mark.asyncio
    async def test_embed_single(self) -> None:
        provider = OllamaEmbeddingProvider()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"embeddings": [[1.0, 2.0, 3.0]]}
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.is_closed = False
        provider._client = mock_client

        result = await provider.embed_single("nomic", "hello")
        assert result == [1.0, 2.0, 3.0]

    @pytest.mark.asyncio
    async def test_embed_single_empty(self) -> None:
        provider = OllamaEmbeddingProvider()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"embeddings": []}
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.is_closed = False
        provider._client = mock_client

        with pytest.raises(ValueError, match="Keine Embeddings"):
            await provider.embed_single("nomic", "hello")

    @pytest.mark.asyncio
    async def test_embed_batch_raw(self) -> None:
        provider = OllamaEmbeddingProvider()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"embeddings": [[1.0], [2.0]]}
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.is_closed = False
        provider._client = mock_client

        result = await provider.embed_batch_raw("nomic", ["a", "b"])
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        provider = OllamaEmbeddingProvider()
        mock_client = AsyncMock()
        mock_client.is_closed = False
        provider._client = mock_client
        await provider.close()
        mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_none(self) -> None:
        provider = OllamaEmbeddingProvider()
        await provider.close()  # should not raise


# ============================================================================
# OpenAICompatibleEmbeddingProvider
# ============================================================================


class TestOpenAICompatibleEmbeddingProvider:
    @pytest.mark.asyncio
    async def test_embed_single(self) -> None:
        provider = OpenAICompatibleEmbeddingProvider(api_key="test-key")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": [{"embedding": [0.1, 0.2], "index": 0}]}
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.is_closed = False
        provider._client = mock_client

        result = await provider.embed_single("text-embedding-3-small", "hello")
        assert result == [0.1, 0.2]

    @pytest.mark.asyncio
    async def test_embed_batch_raw(self) -> None:
        provider = OpenAICompatibleEmbeddingProvider(api_key="test-key")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [
                {"embedding": [0.1], "index": 0},
                {"embedding": [0.2], "index": 1},
            ]
        }
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.is_closed = False
        provider._client = mock_client

        result = await provider.embed_batch_raw("text-embedding-3-small", ["a", "b"])
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        provider = OpenAICompatibleEmbeddingProvider(api_key="k")
        mock_client = AsyncMock()
        mock_client.is_closed = False
        provider._client = mock_client
        await provider.close()
        mock_client.aclose.assert_called_once()


# ============================================================================
# GeminiEmbeddingProvider
# ============================================================================


class TestGeminiEmbeddingProvider:
    @pytest.mark.asyncio
    async def test_embed_single(self) -> None:
        provider = GeminiEmbeddingProvider(api_key="gemini-key")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"embedding": {"values": [0.5, 0.6]}}
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.is_closed = False
        provider._client = mock_client

        result = await provider.embed_single("embedding-001", "hello")
        assert result == [0.5, 0.6]

    @pytest.mark.asyncio
    async def test_embed_batch_raw(self) -> None:
        provider = GeminiEmbeddingProvider(api_key="gemini-key")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"embeddings": [{"values": [0.1]}, {"values": [0.2]}]}
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.is_closed = False
        provider._client = mock_client

        result = await provider.embed_batch_raw("embedding-001", ["a", "b"])
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        provider = GeminiEmbeddingProvider(api_key="k")
        mock_client = AsyncMock()
        mock_client.is_closed = False
        provider._client = mock_client
        await provider.close()
        mock_client.aclose.assert_called_once()


# ============================================================================
# create_embedding_provider factory
# ============================================================================


class TestCreateEmbeddingProvider:
    def test_ollama_backend(self) -> None:
        config = MagicMock()
        config.llm_backend_type = "ollama"
        config.ollama.base_url = "http://localhost:11434"
        config.ollama.timeout_seconds = 30
        provider = create_embedding_provider(config)
        assert isinstance(provider, OllamaEmbeddingProvider)

    def test_gemini_backend(self) -> None:
        config = MagicMock()
        config.llm_backend_type = "gemini"
        config.gemini_api_key = "test-key"
        provider = create_embedding_provider(config)
        assert isinstance(provider, GeminiEmbeddingProvider)

    def test_openai_backend(self) -> None:
        config = MagicMock()
        config.llm_backend_type = "openai"
        config.openai_api_key = "test-key"
        config.openai_base_url = "https://api.openai.com/v1"
        with patch(
            "cognithor.memory.embeddings._get_api_key_and_url",
            return_value=("key", "https://api.openai.com/v1"),
        ):
            provider = create_embedding_provider(config)
            assert isinstance(provider, OpenAICompatibleEmbeddingProvider)

    def test_no_embedding_backend_with_openai_key(self) -> None:
        config = MagicMock()
        config.llm_backend_type = "anthropic"
        config.openai_api_key = "fallback-key"
        config.openai_base_url = "https://api.openai.com/v1"
        provider = create_embedding_provider(config)
        assert isinstance(provider, OpenAICompatibleEmbeddingProvider)

    def test_no_embedding_backend_without_openai_key(self) -> None:
        config = MagicMock()
        config.llm_backend_type = "anthropic"
        config.openai_api_key = ""
        provider = create_embedding_provider(config)
        assert isinstance(provider, NullEmbeddingProvider)

    def test_unknown_backend_fallback(self) -> None:
        config = MagicMock()
        config.llm_backend_type = "totally_unknown"
        config.ollama.base_url = "http://localhost:11434"
        config.ollama.timeout_seconds = 30
        provider = create_embedding_provider(config)
        assert isinstance(provider, OllamaEmbeddingProvider)


# ============================================================================
# EmbeddingClient
# ============================================================================


class TestEmbeddingClient:
    def test_properties(self) -> None:
        client = EmbeddingClient(
            model="test-model", dimensions=128, provider=NullEmbeddingProvider()
        )
        assert client.model == "test-model"
        assert client.dimensions == 128

    def test_load_cache(self) -> None:
        client = EmbeddingClient(provider=NullEmbeddingProvider())
        count = client.load_cache({"hash1": [1.0], "hash2": [2.0]})
        assert count == 2

    def test_get_cached(self) -> None:
        client = EmbeddingClient(provider=NullEmbeddingProvider())
        client.load_cache({"hash1": [1.0, 2.0]})
        assert client.get_cached("hash1") == [1.0, 2.0]
        assert client.get_cached("nonexistent") is None

    def test_cache_put_lru(self) -> None:
        client = EmbeddingClient(provider=NullEmbeddingProvider())
        client._MAX_CACHE_SIZE = 3
        client._cache_put("a", [1.0])
        client._cache_put("b", [2.0])
        client._cache_put("c", [3.0])
        client._cache_put("d", [4.0])  # should evict "a"
        assert client.get_cached("a") is None
        assert client.get_cached("d") == [4.0]

    def test_cache_put_update_existing(self) -> None:
        client = EmbeddingClient(provider=NullEmbeddingProvider())
        client._cache_put("a", [1.0])
        client._cache_put("a", [2.0])
        assert client.get_cached("a") == [2.0]

    @pytest.mark.asyncio
    async def test_embed_text_cached(self) -> None:
        client = EmbeddingClient(model="test", dimensions=2, provider=NullEmbeddingProvider())
        client.load_cache({"hash1": [1.0, 2.0]})
        result = await client.embed_text("hello", content_hash="hash1")
        assert result.cached is True
        assert result.vector == [1.0, 2.0]
        assert client.stats.cache_hits == 1

    @pytest.mark.asyncio
    async def test_embed_text_api_call(self) -> None:
        mock_provider = AsyncMock()
        mock_provider.embed_single = AsyncMock(return_value=[0.5, 0.6])
        client = EmbeddingClient(model="test", dimensions=2, provider=mock_provider)
        result = await client.embed_text("hello", content_hash="new_hash")
        assert result.cached is False
        assert result.vector == [0.5, 0.6]
        assert client.stats.api_calls == 1

    @pytest.mark.asyncio
    async def test_embed_text_no_hash(self) -> None:
        mock_provider = AsyncMock()
        mock_provider.embed_single = AsyncMock(return_value=[0.5])
        client = EmbeddingClient(model="test", dimensions=1, provider=mock_provider)
        result = await client.embed_text("hello")
        assert not result.cached

    @pytest.mark.asyncio
    async def test_embed_text_error(self) -> None:
        mock_provider = AsyncMock()
        mock_provider.embed_single = AsyncMock(side_effect=ValueError("bad"))
        client = EmbeddingClient(model="test", dimensions=1, provider=mock_provider)
        with pytest.raises(ValueError, match="bad"):
            await client.embed_text("hello", content_hash="h")
        assert client.stats.errors == 1

    @pytest.mark.asyncio
    async def test_embed_batch_all_cached(self) -> None:
        client = EmbeddingClient(model="test", dimensions=1, provider=NullEmbeddingProvider())
        client.load_cache({"h1": [1.0], "h2": [2.0]})
        results = await client.embed_batch(["a", "b"], ["h1", "h2"])
        assert len(results) == 2
        assert all(r.cached for r in results)

    @pytest.mark.asyncio
    async def test_embed_batch_mixed(self) -> None:
        mock_provider = AsyncMock()
        mock_provider.embed_batch_raw = AsyncMock(return_value=[[0.9]])
        client = EmbeddingClient(model="test", dimensions=1, provider=mock_provider)
        client.load_cache({"h1": [1.0]})
        results = await client.embed_batch(["a", "b"], ["h1", "h2"])
        assert results[0].cached is True
        assert results[1].cached is False

    @pytest.mark.asyncio
    async def test_embed_batch_length_mismatch(self) -> None:
        client = EmbeddingClient(provider=NullEmbeddingProvider())
        with pytest.raises(ValueError, match="gleich lang"):
            await client.embed_batch(["a", "b"], ["h1"])

    @pytest.mark.asyncio
    async def test_embed_batch_no_hashes(self) -> None:
        mock_provider = AsyncMock()
        mock_provider.embed_batch_raw = AsyncMock(return_value=[[0.1], [0.2]])
        client = EmbeddingClient(model="test", dimensions=1, provider=mock_provider)
        results = await client.embed_batch(["a", "b"])
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_embed_batch_api_error(self) -> None:
        mock_provider = AsyncMock()
        mock_provider.embed_batch_raw = AsyncMock(side_effect=ValueError("batch error"))
        client = EmbeddingClient(model="test", dimensions=1, provider=mock_provider)
        results = await client.embed_batch(["a"], ["h1"])
        # Error results in None
        assert results[0] is None
        assert client.stats.errors == 1

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        mock_provider = AsyncMock()
        client = EmbeddingClient(provider=mock_provider)
        await client.close()
        mock_provider.close.assert_called_once()
