"""Tests for the CLI model registry."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from cognithor.cli.model_registry import _CUSTOM_OPTION, ModelRegistry

# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture()
def registry(tmp_path):
    """Registry backed by a temporary copy of the shipped JSON."""
    from pathlib import Path

    src = Path(__file__).resolve().parents[2] / "src" / "cognithor" / "cli" / "model_registry.json"
    dest = tmp_path / "model_registry.json"
    dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return ModelRegistry(registry_path=dest)


# ------------------------------------------------------------------
# Cached model tests
# ------------------------------------------------------------------

ALL_PROVIDERS = ["ollama", "openai", "anthropic", "gemini", "lmstudio", "claude-code"]


@pytest.mark.parametrize("provider", ALL_PROVIDERS)
def test_cached_models_load(registry, provider):
    models = registry.get_cached_models(provider)
    assert isinstance(models, list)
    assert len(models) >= 1  # at minimum the Custom option


@pytest.mark.parametrize("provider", ALL_PROVIDERS)
def test_cached_models_end_with_custom(registry, provider):
    models = registry.get_cached_models(provider)
    assert models[-1] == _CUSTOM_OPTION


def test_unknown_provider_returns_custom_only(registry):
    models = registry.get_cached_models("nonexistent")
    assert models == [_CUSTOM_OPTION]


def test_ollama_cached_contains_expected(registry):
    models = registry.get_cached_models("ollama")
    assert "qwen3:32b" in models
    assert "deepseek-r1:32b" in models


def test_openai_cached_contains_expected(registry):
    models = registry.get_cached_models("openai")
    assert "gpt-4.1" in models
    assert "o4-mini" in models


# ------------------------------------------------------------------
# Live discovery -- Ollama (mocked)
# ------------------------------------------------------------------

FAKE_OLLAMA_RESPONSE = {
    "models": [
        {"name": "qwen3:32b", "size": 1000},
        {"name": "llama3.3:70b", "size": 2000},
    ]
}


@pytest.mark.asyncio
async def test_ollama_live_discovery(registry):
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = FAKE_OLLAMA_RESPONSE
    mock_resp.raise_for_status = lambda: None

    async def mock_get(url, headers=None):
        return mock_resp

    with patch("cognithor.cli.model_registry.httpx.AsyncClient") as MockClient:
        ctx = AsyncMock()
        ctx.get = mock_get
        MockClient.return_value.__aenter__ = AsyncMock(return_value=ctx)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

        models = await registry.discover_models("ollama")

    assert "qwen3:32b" in models
    assert "llama3.3:70b" in models
    assert models[-1] == _CUSTOM_OPTION


# ------------------------------------------------------------------
# Live discovery -- OpenAI-style (mocked)
# ------------------------------------------------------------------

FAKE_OPENAI_RESPONSE = {
    "data": [
        {"id": "gpt-4.1", "object": "model"},
        {"id": "gpt-4o", "object": "model"},
    ]
}


@pytest.mark.asyncio
async def test_openai_live_discovery(registry):
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = FAKE_OPENAI_RESPONSE
    mock_resp.raise_for_status = lambda: None

    async def mock_get(url, headers=None):
        return mock_resp

    with patch("cognithor.cli.model_registry.httpx.AsyncClient") as MockClient:
        ctx = AsyncMock()
        ctx.get = mock_get
        MockClient.return_value.__aenter__ = AsyncMock(return_value=ctx)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch.dict("os.environ", {"COGNITHOR_OPENAI_API_KEY": "sk-test"}):
            models = await registry.discover_models("openai")

    assert "gpt-4.1" in models
    assert "gpt-4o" in models
    assert models[-1] == _CUSTOM_OPTION


# ------------------------------------------------------------------
# Live discovery -- Gemini (mocked, with generateContent filter)
# ------------------------------------------------------------------

FAKE_GEMINI_RESPONSE = {
    "models": [
        {
            "name": "models/gemini-2.5-pro",
            "supportedGenerationMethods": ["generateContent"],
        },
        {
            "name": "models/embedding-001",
            "supportedGenerationMethods": ["embedContent"],
        },
    ]
}


@pytest.mark.asyncio
async def test_gemini_live_discovery_filters(registry):
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = FAKE_GEMINI_RESPONSE
    mock_resp.raise_for_status = lambda: None

    async def mock_get(url, headers=None):
        return mock_resp

    with patch("cognithor.cli.model_registry.httpx.AsyncClient") as MockClient:
        ctx = AsyncMock()
        ctx.get = mock_get
        MockClient.return_value.__aenter__ = AsyncMock(return_value=ctx)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch.dict("os.environ", {"COGNITHOR_GEMINI_API_KEY": "test-key"}):
            models = await registry.discover_models("gemini")

    assert "gemini-2.5-pro" in models
    assert "embedding-001" not in models
    assert models[-1] == _CUSTOM_OPTION


# ------------------------------------------------------------------
# Fallback on connection error
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fallback_to_cached_on_connection_error(registry):
    with patch("cognithor.cli.model_registry.httpx.AsyncClient") as MockClient:
        ctx = AsyncMock()
        ctx.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
        MockClient.return_value.__aenter__ = AsyncMock(return_value=ctx)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

        models = await registry.discover_models("ollama")

    # Should fall back to cached
    assert "qwen3:32b" in models
    assert models[-1] == _CUSTOM_OPTION


# ------------------------------------------------------------------
# No-discovery providers fall back gracefully
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_discovery_url_returns_cached(registry):
    """Anthropic and claude-code have no discovery URL."""
    models = await registry.discover_models("anthropic")
    assert "claude-sonnet-4-20250514" in models
    assert models[-1] == _CUSTOM_OPTION


@pytest.mark.asyncio
async def test_unknown_provider_discover(registry):
    models = await registry.discover_models("nonexistent")
    assert models == [_CUSTOM_OPTION]


# ------------------------------------------------------------------
# Sync wrapper
# ------------------------------------------------------------------


def test_discover_models_sync(registry):
    with patch("cognithor.cli.model_registry.httpx.AsyncClient") as MockClient:
        ctx = AsyncMock()
        ctx.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        MockClient.return_value.__aenter__ = AsyncMock(return_value=ctx)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

        models = registry.discover_models_sync("ollama")

    assert "qwen3:32b" in models
    assert models[-1] == _CUSTOM_OPTION
