"""Tests for the synchronous LLMClient session bridge."""

import pytest

from pentestgpt_legacy.llm.base import BaseProvider, Message
from pentestgpt_legacy.llm.client import LLMClient
from pentestgpt_legacy.llm.registry import ModelSpec, ProviderInfo

pytestmark = pytest.mark.unit


class FakeProvider(BaseProvider):
    """Records calls and echoes a deterministic reply."""

    def __init__(self) -> None:
        super().__init__(ProviderInfo(key="fake", label="Fake", kind="openai"), None, None)
        self.calls: list[tuple[list[Message], str | None]] = []

    async def acomplete(
        self,
        messages: list[Message],
        system: str | None,
        spec: ModelSpec,
        *,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        self.calls.append(([dict(m) for m in messages], system))
        return f"reply-{len(messages)}"


def _spec(context_window: int = 100_000) -> ModelSpec:
    return ModelSpec(
        id="fake-model", provider="fake", context_window=context_window, tier="balanced"
    )


def test_send_new_message_creates_conversation() -> None:
    provider = FakeProvider()
    client = LLMClient(provider, _spec())
    text, cid = client.send_new_message("hello")
    assert text == "reply-1"
    assert cid in client.conversations
    history = client.conversations[cid]
    assert history[0] == {"role": "user", "content": "hello"}
    assert history[1] == {"role": "assistant", "content": "reply-1"}


def test_send_message_continues_conversation() -> None:
    provider = FakeProvider()
    client = LLMClient(provider, _spec())
    _, cid = client.send_new_message("first")
    client.send_message("second", cid)
    assert len(client.conversations[cid]) == 4
    # second call saw both prior turns + the new user message
    last_messages, _system = provider.calls[-1]
    assert last_messages[0]["role"] == "user"
    assert last_messages[-1] == {"role": "user", "content": "second"}


def test_system_prompt_forwarded() -> None:
    provider = FakeProvider()
    client = LLMClient(provider, _spec(), system_prompt="SYS")
    client.send_new_message("hi")
    _messages, system = provider.calls[-1]
    assert system == "SYS"


def test_history_trimmed_to_length_and_starts_with_user() -> None:
    provider = FakeProvider()
    client = LLMClient(provider, _spec(), history_length=2)
    _, cid = client.send_new_message("turn1")
    for i in range(5):
        client.send_message(f"turn-{i}", cid)
    # the provider only ever received at most history_length messages
    for messages, _system in provider.calls:
        assert len(messages) <= 2
        assert messages[0]["role"] == "user"
