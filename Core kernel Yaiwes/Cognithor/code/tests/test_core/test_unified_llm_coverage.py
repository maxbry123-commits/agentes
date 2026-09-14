"""Coverage-Tests fuer unified_llm.py -- fehlende Zeilen."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cognithor.config import CognithorConfig, ensure_directory_structure
from cognithor.core.unified_llm import UnifiedLLMClient


@pytest.fixture()
def config(tmp_path) -> CognithorConfig:
    cfg = CognithorConfig(cognithor_home=tmp_path)
    ensure_directory_structure(cfg)
    return cfg


# ============================================================================
# UnifiedLLMClient -- Ollama mode
# ============================================================================


class TestUnifiedLLMOllamaMode:
    @pytest.mark.asyncio
    async def test_chat_stream(self, config: CognithorConfig) -> None:
        """Test streaming mode via Ollama."""
        mock_ollama = AsyncMock()

        async def mock_stream(**kwargs):
            for token in ["Hel", "lo"]:
                yield token

        mock_ollama.chat_stream = mock_stream
        mock_ollama.is_available = AsyncMock(return_value=True)

        client = UnifiedLLMClient(ollama_client=mock_ollama)
        chunks = []
        async for chunk in client.chat_stream(
            model="test:7b",
            messages=[{"role": "user", "content": "Hi"}],
        ):
            chunks.append(chunk)
        # Should get streaming chunks plus final done marker
        assert len(chunks) >= 1
        # Last chunk should be done marker
        assert chunks[-1]["done"] is True

    @pytest.mark.asyncio
    async def test_embed_ollama(self, config: CognithorConfig) -> None:
        """Embed via Ollama returns a flat list which gets wrapped in dict."""
        mock_ollama = AsyncMock()
        mock_ollama.embed = AsyncMock(return_value=[0.1, 0.2, 0.3])

        client = UnifiedLLMClient(ollama_client=mock_ollama)
        result = await client.embed("test:7b", "Hello world")
        assert isinstance(result, dict)
        assert "embedding" in result
        assert result["embedding"] == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_list_models(self, config: CognithorConfig) -> None:
        mock_ollama = AsyncMock()
        mock_ollama.list_models = AsyncMock(return_value=["qwen3:32b"])

        client = UnifiedLLMClient(ollama_client=mock_ollama)
        models = await client.list_models()
        assert isinstance(models, list)
        assert "qwen3:32b" in models

    @pytest.mark.asyncio
    async def test_close(self, config: CognithorConfig) -> None:
        mock_ollama = AsyncMock()
        mock_ollama.close = AsyncMock()

        client = UnifiedLLMClient(ollama_client=mock_ollama)
        await client.close()
        mock_ollama.close.assert_awaited_once()

    def test_backend_type_ollama(self) -> None:
        mock_ollama = MagicMock()
        client = UnifiedLLMClient(ollama_client=mock_ollama)
        assert client.backend_type == "ollama"

    @pytest.mark.asyncio
    async def test_is_available_ollama(self) -> None:
        mock_ollama = AsyncMock()
        mock_ollama.is_available = AsyncMock(return_value=True)

        client = UnifiedLLMClient(ollama_client=mock_ollama)
        result = await client.is_available()
        assert result is True

    @pytest.mark.asyncio
    async def test_is_available_no_backend(self) -> None:
        """No backend and no ollama => False."""
        client = UnifiedLLMClient(ollama_client=None, backend=None)
        result = await client.is_available()
        assert result is False

    @pytest.mark.asyncio
    async def test_list_models_no_backend(self) -> None:
        """No backend and no ollama => empty list."""
        client = UnifiedLLMClient(ollama_client=None, backend=None)
        models = await client.list_models()
        assert models == []

    def test_has_embedding_support_ollama(self) -> None:
        mock_ollama = MagicMock()
        client = UnifiedLLMClient(ollama_client=mock_ollama)
        assert client.has_embedding_support is True


# ============================================================================
# UnifiedLLMClient -- Backend mode
# ============================================================================


class TestUnifiedLLMBackendMode:
    @pytest.mark.asyncio
    async def test_chat_with_backend(self) -> None:
        """Backend.chat() returns ChatResponse object (not dict)."""
        from cognithor.core.llm_backend import ChatResponse

        mock_backend = AsyncMock()
        mock_backend.chat = AsyncMock(
            return_value=ChatResponse(
                content="Hello!",
                model="gpt-4",
                tool_calls=None,
                usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            )
        )

        client = UnifiedLLMClient(ollama_client=None, backend=mock_backend)
        result = await client.chat(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hi"}],
        )
        assert "message" in result
        assert result["message"]["content"] == "Hello!"
        assert result["model"] == "gpt-4"
        assert result["done"] is True
        # Usage info should be converted
        assert result.get("prompt_eval_count") == 10
        assert result.get("eval_count") == 5

    @pytest.mark.asyncio
    async def test_chat_with_backend_tool_calls(self) -> None:
        """Backend.chat() returns ChatResponse with tool_calls."""
        from cognithor.core.llm_backend import ChatResponse

        tool_calls = [{"function": {"name": "web_search", "arguments": {"q": "test"}}}]
        mock_backend = AsyncMock()
        mock_backend.chat = AsyncMock(
            return_value=ChatResponse(
                content="",
                model="gpt-4",
                tool_calls=tool_calls,
                usage=None,
            )
        )

        client = UnifiedLLMClient(ollama_client=None, backend=mock_backend)
        result = await client.chat(
            model="gpt-4",
            messages=[{"role": "user", "content": "Search for X"}],
        )
        assert "message" in result
        assert result["message"]["tool_calls"] == tool_calls

    @pytest.mark.asyncio
    async def test_chat_with_backend_error_wraps_to_ollama_error(self) -> None:
        """Backend errors get wrapped as OllamaError."""
        from cognithor.core.model_router import OllamaError

        mock_backend = AsyncMock()
        mock_backend.chat = AsyncMock(side_effect=Exception("API error"))
        mock_backend.backend_type = "openai"

        client = UnifiedLLMClient(ollama_client=None, backend=mock_backend)
        with pytest.raises(OllamaError, match="LLM-Backend-Fehler"):
            await client.chat(
                model="gpt-4",
                messages=[{"role": "user", "content": "Hi"}],
            )

    @pytest.mark.asyncio
    async def test_is_available_with_backend(self) -> None:
        mock_backend = AsyncMock()
        mock_backend.is_available = AsyncMock(return_value=True)

        client = UnifiedLLMClient(ollama_client=None, backend=mock_backend)
        result = await client.is_available()
        assert result is True

    @pytest.mark.asyncio
    async def test_is_available_backend_exception(self) -> None:
        """Backend.is_available() throws => return False."""
        mock_backend = AsyncMock()
        mock_backend.is_available = AsyncMock(side_effect=Exception("down"))

        client = UnifiedLLMClient(ollama_client=None, backend=mock_backend)
        result = await client.is_available()
        assert result is False

    @pytest.mark.asyncio
    async def test_list_models_with_backend(self) -> None:
        mock_backend = AsyncMock()
        mock_backend.list_models = AsyncMock(return_value=["gpt-4", "gpt-3.5-turbo"])

        client = UnifiedLLMClient(ollama_client=None, backend=mock_backend)
        models = await client.list_models()
        assert "gpt-4" in models

    @pytest.mark.asyncio
    async def test_list_models_backend_exception(self) -> None:
        """Backend.list_models() throws => empty list."""
        mock_backend = AsyncMock()
        mock_backend.list_models = AsyncMock(side_effect=Exception("fail"))

        client = UnifiedLLMClient(ollama_client=None, backend=mock_backend)
        models = await client.list_models()
        assert models == []

    @pytest.mark.asyncio
    async def test_embed_with_backend(self) -> None:
        from cognithor.core.llm_backend import EmbedResponse

        mock_backend = AsyncMock()
        mock_backend.embed = AsyncMock(
            return_value=EmbedResponse(
                embedding=[0.1, 0.2, 0.3],
                model="text-embedding-3-small",
            )
        )

        client = UnifiedLLMClient(ollama_client=None, backend=mock_backend)
        result = await client.embed("text-embedding-3-small", "Hello")
        assert isinstance(result, dict)
        assert result["embedding"] == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_close_backend(self) -> None:
        mock_backend = AsyncMock()
        mock_backend.close = AsyncMock()

        client = UnifiedLLMClient(ollama_client=None, backend=mock_backend)
        await client.close()
        mock_backend.close.assert_awaited_once()

    def test_backend_type_from_backend(self) -> None:
        mock_backend = MagicMock()
        mock_backend.backend_type = "openai"

        client = UnifiedLLMClient(ollama_client=None, backend=mock_backend)
        assert client.backend_type == "openai"

    def test_has_embedding_support_anthropic(self) -> None:
        mock_backend = MagicMock()
        mock_backend.backend_type = "anthropic"

        client = UnifiedLLMClient(ollama_client=None, backend=mock_backend)
        assert client.has_embedding_support is False

    @pytest.mark.asyncio
    async def test_chat_stream_with_backend(self) -> None:
        """Streaming via backend."""
        mock_backend = AsyncMock()

        async def mock_stream(**kwargs):
            for token in ["He", "ll", "o"]:
                yield token

        mock_backend.chat_stream = mock_stream

        client = UnifiedLLMClient(ollama_client=None, backend=mock_backend)
        chunks = []
        async for chunk in client.chat_stream(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hi"}],
        ):
            chunks.append(chunk)
        assert len(chunks) >= 1
        assert chunks[-1]["done"] is True

    @pytest.mark.asyncio
    async def test_chat_no_backend_no_ollama_raises(self) -> None:
        """Neither ollama nor backend => OllamaError."""
        from cognithor.core.model_router import OllamaError

        client = UnifiedLLMClient(ollama_client=None, backend=None)
        with pytest.raises(
            OllamaError, match="Kein LLM-Backend|kein.*Backend|no.*backend|nicht verf"
        ):
            await client.chat(
                model="gpt-4",
                messages=[{"role": "user", "content": "Hi"}],
            )

    @pytest.mark.asyncio
    async def test_embed_no_backend_no_ollama_raises(self) -> None:
        from cognithor.core.model_router import OllamaError

        client = UnifiedLLMClient(ollama_client=None, backend=None)
        with pytest.raises(
            OllamaError, match="Kein LLM-Backend|kein.*Backend|no.*backend|nicht verf"
        ):
            await client.embed("model", "text")


# ============================================================================
# Factory
# ============================================================================


class TestUnifiedLLMFactory:
    def test_create_ollama(self, config: CognithorConfig) -> None:
        with patch("cognithor.core.unified_llm.OllamaClient") as MockOllama:
            MockOllama.return_value = MagicMock()
            client = UnifiedLLMClient.create(config)
            assert isinstance(client, UnifiedLLMClient)
            assert client.backend_type == "ollama"

    def test_create_with_backend_type(self, config: CognithorConfig) -> None:
        config.llm_backend_type = "openai"
        with patch("cognithor.core.unified_llm.OllamaClient") as MockOllama:
            MockOllama.return_value = MagicMock()
            with patch("cognithor.core.llm_backend.create_backend") as mock_create:
                mock_backend = MagicMock()
                mock_backend.backend_type = "openai"
                mock_create.return_value = mock_backend
                client = UnifiedLLMClient.create(config)
                assert isinstance(client, UnifiedLLMClient)

    def test_create_backend_failure_raises(self, config: CognithorConfig) -> None:
        """If backend creation fails, raise OllamaError (no silent fallback)."""
        from cognithor.core.model_router import OllamaError

        config.llm_backend_type = "openai"
        with patch("cognithor.core.llm_backend.create_backend", side_effect=Exception("fail")):
            with pytest.raises(OllamaError, match="konnte nicht initialisiert werden"):
                UnifiedLLMClient.create(config)
