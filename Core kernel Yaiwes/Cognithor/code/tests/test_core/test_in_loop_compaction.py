"""Tests for in-loop compaction (mid-session summarization)."""

from __future__ import annotations

import pytest

from cognithor.core.in_loop_compaction import (
    PROTECT_HEAD_MESSAGES,
    PROTECT_TAIL_MESSAGES,
    SUMMARY_LABEL,
    compact_in_loop,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_history(n: int, *, system_count: int = 0) -> list[dict]:
    """Build a synthetic conversation of *n* user/assistant pairs plus
    *system_count* leading system messages."""
    msgs: list[dict] = [{"role": "system", "content": f"system-{i}"} for i in range(system_count)]
    for i in range(n):
        msgs.append({"role": "user", "content": f"user-{i}"})
        msgs.append({"role": "assistant", "content": f"assistant-{i}"})
    return msgs


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_compaction_when_history_is_short():
    """Short conversations must pass through unchanged."""
    history = _make_history(4)  # 8 body messages — below threshold
    result = await compact_in_loop(history)

    assert result.changed is False
    assert result.compacted_messages == 0
    assert result.summary_source == "none"
    assert result.history is history  # identity check — no copy


@pytest.mark.asyncio
async def test_heuristic_fallback_when_no_summarize_fn():
    """When *summarize_fn* is None the heuristic path must be used."""
    history = _make_history(12)  # 24 body messages — well above threshold
    result = await compact_in_loop(history)

    assert result.changed is True
    assert result.compacted_messages > 0
    assert result.summary_source == "heuristic"
    # The summary message must carry the label
    summaries = [m for m in result.history if SUMMARY_LABEL in m.get("content", "")]
    assert len(summaries) == 1


@pytest.mark.asyncio
async def test_llm_summarization_with_mock():
    """A working *summarize_fn* should produce an LLM summary."""
    history = _make_history(12)

    async def mock_summarize(messages, max_tokens):
        return "LLM produced summary of the middle."

    result = await compact_in_loop(history, summarize_fn=mock_summarize)

    assert result.changed is True
    assert result.summary_source == "llm"
    summaries = [m for m in result.history if SUMMARY_LABEL in m.get("content", "")]
    assert len(summaries) == 1
    assert "LLM produced summary" in summaries[0]["content"]


@pytest.mark.asyncio
async def test_llm_failure_falls_back_to_heuristic():
    """If *summarize_fn* raises, fallback to heuristic."""
    history = _make_history(12)

    async def failing_summarize(messages, max_tokens):
        raise RuntimeError("LLM unavailable")

    result = await compact_in_loop(history, summarize_fn=failing_summarize)

    assert result.changed is True
    assert result.summary_source == "heuristic"
    assert result.compacted_messages > 0


@pytest.mark.asyncio
async def test_llm_empty_response_falls_back_to_heuristic():
    """If *summarize_fn* returns empty string, fallback to heuristic."""
    history = _make_history(12)

    async def empty_summarize(messages, max_tokens):
        return "   "

    result = await compact_in_loop(history, summarize_fn=empty_summarize)

    assert result.changed is True
    assert result.summary_source == "heuristic"


@pytest.mark.asyncio
async def test_system_messages_preserved_in_head():
    """Leading system messages must always appear in the compacted output."""
    history = _make_history(12, system_count=3)
    result = await compact_in_loop(history)

    assert result.changed is True
    # First 3 messages must still be the system messages
    for i in range(3):
        assert result.history[i]["role"] == "system"
        assert result.history[i]["content"] == f"system-{i}"


@pytest.mark.asyncio
async def test_tail_messages_preserved():
    """The last PROTECT_TAIL_MESSAGES body messages must survive compaction."""
    history = _make_history(12)
    original_tail = history[-PROTECT_TAIL_MESSAGES:]

    result = await compact_in_loop(history)

    assert result.changed is True
    # Tail of the compacted history must match original tail
    assert result.history[-PROTECT_TAIL_MESSAGES:] == original_tail


@pytest.mark.asyncio
async def test_head_body_messages_preserved():
    """The first PROTECT_HEAD_MESSAGES body messages must survive compaction."""
    history = _make_history(12, system_count=2)
    # Body starts after system messages
    body_start = 2
    original_head_body = history[body_start : body_start + PROTECT_HEAD_MESSAGES]

    result = await compact_in_loop(history)

    assert result.changed is True
    # After system messages, the next PROTECT_HEAD_MESSAGES must be unchanged
    for i, msg in enumerate(original_head_body):
        assert result.history[body_start + i] == msg


@pytest.mark.asyncio
async def test_compacted_history_is_shorter():
    """The compacted history must be shorter than the original."""
    history = _make_history(20)
    result = await compact_in_loop(history)

    assert result.changed is True
    assert len(result.history) < len(history)
