"""Aux-LLM stuck-adjudication for the browser sub-agent."""

import asyncio

from backend.apps.agents.browser.browser_validator import adjudicate_stuck, extract_text


class p_Block:
    def __init__(self, type_, text=""):
        self.type = type_
        self.text = text


class p_Resp:
    def __init__(self, blocks):
        self.content = blocks


class p_FakeClient:
    """Minimal Anthropic-shaped client: client.messages.create(...)."""

    def __init__(self, resp=None, raise_exc=None):
        self.p_resp = resp
        self.p_raise = raise_exc
        self.calls = []
        self.messages = self

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.p_raise:
            raise self.p_raise
        return self.p_resp


def test_returns_extracted_guidance_and_assembles_prompt():
    fc = p_FakeClient(resp=p_Resp([p_Block("text", "Press Tab then Enter to focus the field.")]))
    out = asyncio.run(adjudicate_stuck(fc, "cheap-model", "share the doc", "- click -> not found", "the page"))
    assert out == "Press Tab then Enter to focus the field."
    call = fc.calls[0]
    assert call["model"] == "cheap-model"
    assert call["max_tokens"] == 300
    prompt = call["messages"][0]["content"]
    assert "share the doc" in prompt
    assert "not found" in prompt


def test_swallows_provider_error_and_returns_empty():
    fc = p_FakeClient(raise_exc=RuntimeError("429 rate limited"))
    out = asyncio.run(adjudicate_stuck(fc, "m", "g", "r", "p"))
    assert out == ""


def test_extract_text_joins_text_blocks_and_ignores_others():
    resp = p_Resp([p_Block("text", "First."), p_Block("tool_use"), p_Block("text", "Second.")])
    assert extract_text(resp) == "First. Second."


def test_handles_empty_inputs_without_crashing():
    fc = p_FakeClient(resp=p_Resp([p_Block("text", "ok")]))
    out = asyncio.run(adjudicate_stuck(fc, "m", "", "", ""))
    assert out == "ok"
    # placeholders keep the prompt well-formed
    prompt = fc.calls[0]["messages"][0]["content"]
    assert "(unknown)" in prompt and "(none)" in prompt and "(empty)" in prompt
