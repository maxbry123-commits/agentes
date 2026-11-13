"""Tests for the provider/client factory."""

import pytest

from pentestgpt_legacy.llm import factory
from pentestgpt_legacy.llm.config import LLMSettings
from pentestgpt_legacy.llm.factory import (
    MissingCredentialsError,
    UnknownModelError,
    get_client,
    list_models,
)
from pentestgpt_legacy.llm.providers import (
    AnthropicProvider,
    OpenAICompatibleProvider,
)

pytestmark = pytest.mark.unit


def _settings(**kwargs: str) -> LLMSettings:
    return LLMSettings(_env_file=None, **kwargs)


def test_get_client_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory, "get_settings", lambda: _settings(openai_api_key="sk-x"))
    client = get_client("gpt-5.5")
    assert isinstance(client.provider, OpenAICompatibleProvider)
    assert client.spec.id == "gpt-5.5"
    assert client.provider.base_url is None  # OpenAI uses SDK default


def test_get_client_deepseek_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory, "get_settings", lambda: _settings(deepseek_api_key="sk-d"))
    client = get_client("deepseek-v4-flash")
    assert isinstance(client.provider, OpenAICompatibleProvider)
    assert client.provider.base_url == "https://api.deepseek.com"


def test_get_client_anthropic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory, "get_settings", lambda: _settings(anthropic_api_key="sk-a"))
    client = get_client("claude-opus-4-8")
    assert isinstance(client.provider, AnthropicProvider)


def test_get_client_unknown_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory, "get_settings", lambda: _settings(openai_api_key="x"))
    with pytest.raises(UnknownModelError):
        get_client("no-such-model")


def test_get_client_missing_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory, "get_settings", lambda: _settings())  # no keys
    with pytest.raises(MissingCredentialsError):
        get_client("gemini-3.1-pro")


def test_get_client_ollama_no_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory, "get_settings", lambda: _settings())
    client = get_client("ollama:qwen3")
    assert client.spec.api_id == "qwen3"
    assert client.provider.base_url == "http://localhost:11434/v1"


def test_list_models_nonempty() -> None:
    assert list_models()
