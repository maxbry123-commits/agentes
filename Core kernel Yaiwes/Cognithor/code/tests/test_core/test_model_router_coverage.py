"""Coverage-Tests fuer model_router.py -- fehlende Zeilen."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from cognithor.config import CognithorConfig, ensure_directory_structure
from cognithor.core.model_router import ModelRouter, OllamaClient, OllamaError
from cognithor.models import Message, MessageRole


@pytest.fixture()
def config(tmp_path) -> CognithorConfig:
    cfg = CognithorConfig(cognithor_home=tmp_path)
    ensure_directory_structure(cfg)
    return cfg


def _mock_ollama_client(config: CognithorConfig) -> MagicMock:
    """Create a mock OllamaClient without needing real httpx connections."""
    mock = MagicMock(spec=OllamaClient)
    mock.list_models = AsyncMock(return_value=["qwen3:32b", "qwen3:8b"])
    mock.is_available = AsyncMock(return_value=True)
    mock.chat = AsyncMock(
        return_value={
            "message": {"role": "assistant", "content": "Hello"},
        }
    )
    return mock


# ============================================================================
# OllamaError
# ============================================================================


class TestOllamaError:
    def test_ollama_error(self) -> None:
        err = OllamaError("test error", status_code=500)
        assert str(err) == "test error"
        assert err.status_code == 500

    def test_ollama_error_no_status(self) -> None:
        err = OllamaError("test error")
        assert err.status_code is None


# ============================================================================
# ModelRouter
# ============================================================================


class TestModelRouterCoverage:
    @pytest.fixture(autouse=True)
    def _reset_coding_override(self):
        """Reset ContextVar before/after each test to prevent cross-test contamination."""
        from cognithor.core.model_router import _coding_override_var

        _coding_override_var.set(None)
        yield
        _coding_override_var.set(None)

    def test_select_model_planning(self, config: CognithorConfig) -> None:
        mock = _mock_ollama_client(config)
        router = ModelRouter(config, mock)
        model = router.select_model("planning", "high")
        assert isinstance(model, str)
        assert len(model) > 0

    def test_select_model_execution(self, config: CognithorConfig) -> None:
        mock = _mock_ollama_client(config)
        router = ModelRouter(config, mock)
        model = router.select_model("simple_tool_call", "low")
        assert isinstance(model, str)

    def test_select_model_code(self, config: CognithorConfig) -> None:
        mock = _mock_ollama_client(config)
        router = ModelRouter(config, mock)
        model = router.select_model("code", "high")
        assert isinstance(model, str)

    def test_select_model_code_low(self, config: CognithorConfig) -> None:
        mock = _mock_ollama_client(config)
        router = ModelRouter(config, mock)
        model = router.select_model("code", "low")
        assert isinstance(model, str)

    def test_select_model_embedding(self, config: CognithorConfig) -> None:
        mock = _mock_ollama_client(config)
        router = ModelRouter(config, mock)
        model = router.select_model("embedding", "low")
        assert isinstance(model, str)

    def test_select_model_unknown_task_high(self, config: CognithorConfig) -> None:
        mock = _mock_ollama_client(config)
        router = ModelRouter(config, mock)
        model = router.select_model("unknown_task", "high")
        assert isinstance(model, str)

    def test_select_model_unknown_task_low(self, config: CognithorConfig) -> None:
        mock = _mock_ollama_client(config)
        router = ModelRouter(config, mock)
        model = router.select_model("unknown_task", "low")
        assert isinstance(model, str)

    def test_set_and_clear_coding_override(self, config: CognithorConfig) -> None:
        mock = _mock_ollama_client(config)
        router = ModelRouter(config, mock)
        router.set_coding_override("deepseek-coder:33b")
        assert router._coding_override == "deepseek-coder:33b"
        router.clear_coding_override()
        assert router._coding_override is None

    def test_coding_override_affects_selection(self, config: CognithorConfig) -> None:
        mock = _mock_ollama_client(config)
        router = ModelRouter(config, mock)
        router.set_coding_override("deepseek-coder:33b")
        model = router.select_model("planning", "high")
        assert model == "deepseek-coder:33b"

    def test_coding_override_not_applied_to_embedding(self, config: CognithorConfig) -> None:
        mock = _mock_ollama_client(config)
        router = ModelRouter(config, mock)
        router.set_coding_override("deepseek-coder:33b")
        model = router.select_model("embedding", "low")
        assert model != "deepseek-coder:33b"

    def test_get_model_config_known(self, config: CognithorConfig) -> None:
        mock = _mock_ollama_client(config)
        router = ModelRouter(config, mock)
        planner_name = config.models.planner.name
        cfg = router.get_model_config(planner_name)
        assert isinstance(cfg, dict)
        assert "temperature" in cfg
        assert "top_p" in cfg
        assert "context_window" in cfg

    def test_get_model_config_unknown(self, config: CognithorConfig) -> None:
        mock = _mock_ollama_client(config)
        router = ModelRouter(config, mock)
        cfg = router.get_model_config("nonexistent:model")
        assert isinstance(cfg, dict)
        assert cfg["temperature"] == 0.7

    @pytest.mark.asyncio
    async def test_initialize_ollama(self, config: CognithorConfig) -> None:
        mock = _mock_ollama_client(config)
        router = ModelRouter(config, mock)
        await router.initialize()
        assert len(router._available_models) > 0

    @pytest.mark.asyncio
    async def test_initialize_with_backend(self, config: CognithorConfig) -> None:
        mock = _mock_ollama_client(config)
        router = ModelRouter(config, mock)
        mock_backend = AsyncMock()
        mock_backend.list_models = AsyncMock(return_value=["gpt-4", "gpt-3.5-turbo"])
        router._backend = mock_backend

        await router.initialize()
        assert "gpt-4" in router._available_models

    def test_from_backend(self, config: CognithorConfig) -> None:
        mock_backend = MagicMock()
        mock_backend.backend_name = "openai"
        router = ModelRouter.from_backend(config, mock_backend)
        assert isinstance(router, ModelRouter)
        assert router.backend is mock_backend

    def test_find_fallback_with_available(self, config: CognithorConfig) -> None:
        mock = _mock_ollama_client(config)
        router = ModelRouter(config, mock)
        router._available_models = {"qwen3:32b", "qwen3:8b"}
        fallback = router._find_fallback("nonexistent:model")
        assert fallback is not None
        assert fallback in router._available_models

    def test_find_fallback_empty(self, config: CognithorConfig) -> None:
        mock = _mock_ollama_client(config)
        router = ModelRouter(config, mock)
        router._available_models = set()
        fallback = router._find_fallback("nonexistent:model")
        assert fallback is None

    def test_select_model_fallback_when_not_available(self, config: CognithorConfig) -> None:
        mock = _mock_ollama_client(config)
        router = ModelRouter(config, mock)
        router._available_models = {"other-model:7b"}
        model = router.select_model("planning", "high")
        assert isinstance(model, str)


# ============================================================================
# OllamaClient
# ============================================================================


class TestOllamaClientCoverage:
    @pytest.mark.asyncio
    async def test_chat(self, config: CognithorConfig) -> None:
        client = OllamaClient(config)
        mock_http = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "message": {"role": "assistant", "content": "Hello"},
            "eval_count": 10,
        }
        mock_http.post = AsyncMock(return_value=mock_resp)
        mock_http.is_closed = False
        client._client = mock_http

        result = await client.chat(
            model="qwen3:32b",
            messages=[{"role": "user", "content": "Hi"}],
        )
        assert "message" in result

    @pytest.mark.asyncio
    async def test_chat_http_error(self, config: CognithorConfig) -> None:
        client = OllamaClient(config)
        mock_http = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mock_http.post = AsyncMock(return_value=mock_resp)
        mock_http.is_closed = False
        client._client = mock_http

        with pytest.raises(OllamaError, match="HTTP 500"):
            await client.chat(
                model="qwen3:32b",
                messages=[{"role": "user", "content": "Hi"}],
            )

    @pytest.mark.asyncio
    async def test_is_available_true(self, config: CognithorConfig) -> None:
        client = OllamaClient(config)
        mock_http = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_http.get = AsyncMock(return_value=mock_resp)
        mock_http.is_closed = False
        client._client = mock_http

        result = await client.is_available()
        assert result is True

    @pytest.mark.asyncio
    async def test_is_available_fail(self, config: CognithorConfig) -> None:
        client = OllamaClient(config)
        mock_http = AsyncMock()
        mock_http.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
        mock_http.is_closed = False
        client._client = mock_http

        result = await client.is_available()
        assert result is False

    @pytest.mark.asyncio
    async def test_list_models(self, config: CognithorConfig) -> None:
        client = OllamaClient(config)
        mock_http = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "models": [{"name": "qwen3:32b"}, {"name": "qwen3:8b"}],
        }
        mock_resp.raise_for_status = MagicMock()
        mock_http.get = AsyncMock(return_value=mock_resp)
        mock_http.is_closed = False
        client._client = mock_http

        models = await client.list_models()
        assert "qwen3:32b" in models
        assert "qwen3:8b" in models

    @pytest.mark.asyncio
    async def test_list_models_error(self, config: CognithorConfig) -> None:
        client = OllamaClient(config)
        mock_http = AsyncMock()
        mock_http.get = AsyncMock(side_effect=Exception("fail"))
        mock_http.is_closed = False
        client._client = mock_http

        models = await client.list_models()
        assert models == []

    @pytest.mark.asyncio
    async def test_close(self, config: CognithorConfig) -> None:
        client = OllamaClient(config)
        mock_http = MagicMock()
        mock_http.is_closed = False
        mock_http.aclose = AsyncMock()
        client._client = mock_http

        await client.close()
        mock_http.aclose.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_close_already_closed(self, config: CognithorConfig) -> None:
        client = OllamaClient(config)
        client._client = None
        await client.close()


# ============================================================================
# messages_to_ollama
# ============================================================================


class TestMessagesToOllama:
    def test_convert_messages(self) -> None:
        from cognithor.core.model_router import messages_to_ollama

        msgs = [
            Message(role=MessageRole.SYSTEM, content="You are helpful."),
            Message(role=MessageRole.USER, content="Hi"),
            Message(role=MessageRole.ASSISTANT, content="Hello!"),
        ]
        result = messages_to_ollama(msgs)
        assert len(result) == 3
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"
        assert result[2]["role"] == "assistant"
