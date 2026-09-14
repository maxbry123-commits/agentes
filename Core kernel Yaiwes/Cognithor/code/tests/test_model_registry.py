"""Tests for cognithor.cli.model_registry -- model discovery and cache."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest

from cognithor.cli.model_registry import _CUSTOM_OPTION, _REGISTRY_PATH, ModelRegistry

if TYPE_CHECKING:
    from pathlib import Path

# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture()
def tmp_registry(tmp_path: Path) -> Path:
    """Create a minimal model_registry.json in tmp."""
    data = {
        "updated": "2026-01-01",
        "providers": {
            "ollama": {
                "discovery_url": "http://localhost:11434/api/tags",
                "models": ["qwen3:32b", "llama3.2:8b"],
            },
            "openai": {
                "discovery_url": "https://api.openai.com/v1/models",
                "api_key_env": "COGNITHOR_OPENAI_API_KEY",
                "models": ["gpt-4o", "gpt-4o-mini"],
            },
        },
    }
    p = tmp_path / "model_registry.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


# ------------------------------------------------------------------
# Cached access
# ------------------------------------------------------------------


class TestGetCachedModels:
    def test_known_provider(self, tmp_registry: Path) -> None:
        reg = ModelRegistry(tmp_registry)
        models = reg.get_cached_models("ollama")
        assert "qwen3:32b" in models
        assert "llama3.2:8b" in models
        assert models[-1] == _CUSTOM_OPTION

    def test_unknown_provider_returns_custom_only(self, tmp_registry: Path) -> None:
        reg = ModelRegistry(tmp_registry)
        models = reg.get_cached_models("unknown_provider")
        assert models == [_CUSTOM_OPTION]

    def test_custom_option_always_last(self, tmp_registry: Path) -> None:
        reg = ModelRegistry(tmp_registry)
        for provider in ("ollama", "openai"):
            models = reg.get_cached_models(provider)
            assert models[-1] == _CUSTOM_OPTION


# ------------------------------------------------------------------
# Live discovery
# ------------------------------------------------------------------


class TestDiscoverModels:
    @pytest.mark.asyncio
    async def test_fallback_on_error(self, tmp_registry: Path) -> None:
        reg = ModelRegistry(tmp_registry)
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(side_effect=Exception("fail"))
            mock_client.return_value.__aexit__ = AsyncMock()
            models = await reg.discover_models("ollama")
        # Should fall back to cached
        assert "qwen3:32b" in models

    @pytest.mark.asyncio
    async def test_no_discovery_url(self, tmp_path: Path) -> None:
        data = {
            "updated": "2026-01-01",
            "providers": {"custom": {"models": ["m1"]}},
        }
        p = tmp_path / "reg.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        reg = ModelRegistry(p)
        models = await reg.discover_models("custom")
        assert "m1" in models
        assert models[-1] == _CUSTOM_OPTION

    @pytest.mark.asyncio
    async def test_unknown_provider(self, tmp_registry: Path) -> None:
        reg = ModelRegistry(tmp_registry)
        models = await reg.discover_models("nope")
        assert models == [_CUSTOM_OPTION]


# ------------------------------------------------------------------
# Sync wrapper
# ------------------------------------------------------------------


class TestDiscoverModelsSync:
    def test_sync_returns_list(self, tmp_registry: Path) -> None:
        reg = ModelRegistry(tmp_registry)
        # Will fail live discovery (no server), fall back to cache
        models = reg.discover_models_sync("ollama")
        assert isinstance(models, list)
        assert len(models) >= 2


# ------------------------------------------------------------------
# Parse response
# ------------------------------------------------------------------


class TestParseResponse:
    def test_ollama(self) -> None:
        payload = {"models": [{"name": "m1"}, {"name": "m2"}]}
        assert ModelRegistry._parse_response("ollama", payload) == ["m1", "m2"]

    def test_openai(self) -> None:
        payload = {"data": [{"id": "gpt-4o"}, {"id": "gpt-4o-mini"}]}
        assert ModelRegistry._parse_response("openai", payload) == ["gpt-4o", "gpt-4o-mini"]

    def test_lmstudio(self) -> None:
        payload = {"data": [{"id": "local-model"}]}
        assert ModelRegistry._parse_response("lmstudio", payload) == ["local-model"]

    def test_gemini(self) -> None:
        payload = {
            "models": [
                {
                    "name": "models/gemini-pro",
                    "supportedGenerationMethods": ["generateContent"],
                },
                {
                    "name": "models/embedding-001",
                    "supportedGenerationMethods": ["embedContent"],
                },
            ]
        }
        result = ModelRegistry._parse_response("gemini", payload)
        assert result == ["gemini-pro"]

    def test_unknown_provider(self) -> None:
        assert ModelRegistry._parse_response("exotic", {}) == []


# ------------------------------------------------------------------
# Registry path
# ------------------------------------------------------------------


def test_default_registry_exists() -> None:
    assert _REGISTRY_PATH.exists(), f"Expected {_REGISTRY_PATH} to exist"


def test_default_registry_valid_json() -> None:
    data = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    assert "providers" in data
    assert "updated" in data
