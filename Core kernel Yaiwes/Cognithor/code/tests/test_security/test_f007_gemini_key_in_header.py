"""Tests fuer F-007: Gemini API Key muss via Header statt URL Query-String gesendet werden.

Prueft dass:
  - GeminiBackend den API-Key als x-goog-api-key Header setzt
  - Keine URL-Konstruktion ?key= enthaelt (Source-Inspection)
  - GeminiEmbeddingProvider den API-Key ebenfalls als Header setzt
  - Der Header tatsaechlich im httpx-Client konfiguriert ist
"""

from __future__ import annotations

import inspect

import pytest


class TestGeminiBackendKeyInHeader:
    """Prueft dass GeminiBackend den API-Key nur via Header sendet."""

    def test_no_key_in_url_source(self) -> None:
        """Source-Code darf kein '?key=' in URL-Konstruktionen enthalten."""
        from cognithor.core.llm_backend import GeminiBackend

        source = inspect.getsource(GeminiBackend)
        # Alle Zeilen mit URL-Konstruktion pruefen
        for i, line in enumerate(source.splitlines(), 1):
            if "?key=" in line and "url" in line.lower():
                pytest.fail(f"GeminiBackend Zeile {i}: API-Key in URL gefunden: {line.strip()}")

    def test_header_set_in_client(self) -> None:
        """_ensure_client() muss x-goog-api-key Header setzen."""
        from cognithor.core.llm_backend import GeminiBackend

        source = inspect.getsource(GeminiBackend._ensure_client)
        assert "x-goog-api-key" in source, "_ensure_client() muss x-goog-api-key Header setzen"

    @pytest.mark.asyncio
    async def test_client_has_header(self) -> None:
        """Der erstellte httpx-Client muss den x-goog-api-key Header haben."""
        from cognithor.core.llm_backend import GeminiBackend

        backend = GeminiBackend(api_key="test-gemini-key-12345", timeout=10)
        client = await backend._ensure_client()
        try:
            assert "x-goog-api-key" in client.headers
            assert client.headers["x-goog-api-key"] == "test-gemini-key-12345"
        finally:
            await client.aclose()

    def test_generate_url_has_no_key(self) -> None:
        """generateContent URL darf keinen ?key= Parameter haben."""
        from cognithor.core.llm_backend import GeminiBackend

        source = inspect.getsource(GeminiBackend)
        for line in source.splitlines():
            if "generateContent" in line and "key=" in line:
                pytest.fail(f"API-Key in generateContent URL: {line.strip()}")

    def test_stream_url_has_no_key(self) -> None:
        """streamGenerateContent URL darf keinen key= Parameter haben."""
        from cognithor.core.llm_backend import GeminiBackend

        source = inspect.getsource(GeminiBackend)
        for line in source.splitlines():
            if "streamGenerateContent" in line and "key=" in line:
                pytest.fail(f"API-Key in stream URL: {line.strip()}")

    def test_embed_url_has_no_key(self) -> None:
        """embedContent URL darf keinen ?key= Parameter haben."""
        from cognithor.core.llm_backend import GeminiBackend

        source = inspect.getsource(GeminiBackend)
        for line in source.splitlines():
            if "embedContent" in line and "key=" in line:
                pytest.fail(f"API-Key in embed URL: {line.strip()}")

    def test_models_url_has_no_key(self) -> None:
        """models-Listing URL darf keinen ?key= Parameter haben."""
        from cognithor.core.llm_backend import GeminiBackend

        source = inspect.getsource(GeminiBackend)
        for line in source.splitlines():
            if "API_URL}/models" in line and "key=" in line:
                pytest.fail(f"API-Key in models URL: {line.strip()}")


class TestGeminiEmbeddingProviderKeyInHeader:
    """Prueft dass GeminiEmbeddingProvider den API-Key nur via Header sendet."""

    def test_no_key_in_url_source(self) -> None:
        """Source-Code darf kein '?key=' enthalten."""
        from cognithor.memory.embeddings import GeminiEmbeddingProvider

        source = inspect.getsource(GeminiEmbeddingProvider)
        for i, line in enumerate(source.splitlines(), 1):
            if "?key=" in line and "url" in line.lower():
                pytest.fail(f"GeminiEmbeddingProvider Zeile {i}: API-Key in URL: {line.strip()}")

    def test_header_set_in_client(self) -> None:
        """_get_client() muss x-goog-api-key Header setzen."""
        from cognithor.memory.embeddings import GeminiEmbeddingProvider

        source = inspect.getsource(GeminiEmbeddingProvider._get_client)
        assert "x-goog-api-key" in source, "_get_client() muss x-goog-api-key Header setzen"

    @pytest.mark.asyncio
    async def test_client_has_header(self) -> None:
        """Der erstellte httpx-Client muss den x-goog-api-key Header haben."""
        from cognithor.memory.embeddings import GeminiEmbeddingProvider

        provider = GeminiEmbeddingProvider(api_key="test-embed-key-67890")
        client = await provider._get_client()
        try:
            assert "x-goog-api-key" in client.headers
            assert client.headers["x-goog-api-key"] == "test-embed-key-67890"
        finally:
            await client.aclose()

    def test_embed_single_url_has_no_key(self) -> None:
        """embed_single URL darf keinen ?key= Parameter haben."""
        from cognithor.memory.embeddings import GeminiEmbeddingProvider

        source = inspect.getsource(GeminiEmbeddingProvider.embed_single)
        assert "?key=" not in source

    def test_embed_batch_url_has_no_key(self) -> None:
        """embed_batch_raw URL darf keinen ?key= Parameter haben."""
        from cognithor.memory.embeddings import GeminiEmbeddingProvider

        source = inspect.getsource(GeminiEmbeddingProvider.embed_batch_raw)
        assert "?key=" not in source
