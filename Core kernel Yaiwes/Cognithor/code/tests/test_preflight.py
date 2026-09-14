"""Tests for context-window preflight check."""

from __future__ import annotations

import pytest

from cognithor.core.preflight import (
    ContextWindowExceeded,
    _compact_messages,
    estimate_tokens,
    preflight_check,
)

# ---------------------------------------------------------------------------
# estimate_tokens
# ---------------------------------------------------------------------------


class TestEstimateTokens:
    def test_empty(self):
        assert estimate_tokens() == 1  # min 1

    def test_system_only(self):
        tokens = estimate_tokens(system="Hello world")
        assert tokens > 0
        assert tokens < 50  # ~11 bytes / 4 ≈ 2-3

    def test_messages(self):
        msgs = [
            {"role": "user", "content": "What is 2+2?"},
            {"role": "assistant", "content": "4"},
        ]
        tokens = estimate_tokens(messages=msgs)
        assert tokens > 10
        assert tokens < 200

    def test_with_tools(self):
        msgs = [{"role": "user", "content": "hi"}]
        tools = [{"name": "web_search", "description": "Search the web", "parameters": {}}]
        without = estimate_tokens(messages=msgs)
        with_tools = estimate_tokens(messages=msgs, tools=tools)
        assert with_tools > without

    def test_unicode_content(self):
        """German/CJK content should produce reasonable estimates."""
        msgs = [{"role": "user", "content": "Wie geht es dir heute?"}]
        tokens = estimate_tokens(messages=msgs)
        assert tokens > 5


# ---------------------------------------------------------------------------
# preflight_check
# ---------------------------------------------------------------------------


class TestPreflightCheck:
    def test_ok_under_threshold(self):
        """Normal request well under limit."""
        msgs = [{"role": "user", "content": "Hello"}]
        result = preflight_check("test-model", msgs, context_window=32768)
        assert result.ok is True
        assert result.usage_pct < 0.8
        assert result.compacted is False
        assert result.dropped_count == 0

    def test_warning_zone(self):
        """Request at 80-100% triggers warning but allows."""
        # Create messages that fill ~85% of a small context window
        content = "x" * 3000  # ~750 tokens
        msgs = [{"role": "user", "content": content}]
        result = preflight_check("test-model", msgs, context_window=1200, max_output_tokens=200)
        assert result.ok is True
        assert result.usage_pct > 0.5  # should be in warning zone or above

    def test_exceeded_auto_compacts(self):
        """Over limit with enough messages to compact."""
        # 20 messages, each ~250 tokens → ~5000 total, window = 3000
        msgs = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": "a" * 1000}
            for i in range(20)
        ]
        original_count = len(msgs)

        result = preflight_check("test-model", msgs, context_window=3000, max_output_tokens=200)
        assert result.ok is True
        assert result.compacted is True
        assert result.dropped_count > 0
        assert len(msgs) < original_count

    def test_exceeded_unrecoverable(self):
        """Single massive message that can't be compacted."""
        # One huge system message > context window
        msgs = [{"role": "system", "content": "x" * 100000}]
        with pytest.raises(ContextWindowExceeded) as exc_info:
            preflight_check("test-model", msgs, context_window=1000, max_output_tokens=100)
        assert exc_info.value.model == "test-model"
        assert exc_info.value.estimated > exc_info.value.limit

    def test_unknown_model_skips(self):
        """Context window = 0 (unknown model) skips check entirely."""
        msgs = [{"role": "user", "content": "x" * 100000}]
        result = preflight_check("unknown-model", msgs, context_window=0)
        assert result.ok is True

    def test_auto_compact_disabled(self):
        """When auto_compact=False, raises immediately on overflow."""
        msgs = [{"role": "user", "content": "x" * 10000}]
        with pytest.raises(ContextWindowExceeded):
            preflight_check(
                "test-model",
                msgs,
                context_window=500,
                max_output_tokens=100,
                auto_compact=False,
            )

    def test_preserves_system_messages(self):
        """System messages are never dropped during compaction."""
        msgs = [
            {"role": "system", "content": "You are a helpful assistant."},
            *[
                {"role": "user" if i % 2 == 0 else "assistant", "content": "a" * 500}
                for i in range(16)
            ],
        ]
        preflight_check("test-model", msgs, context_window=2000, max_output_tokens=200)
        # System message must survive
        assert msgs[0]["role"] == "system"
        assert "helpful assistant" in msgs[0]["content"]

    def test_preserves_recent_messages(self):
        """Last messages are preserved, oldest are dropped."""
        msgs = [
            {"role": "user", "content": f"message-{i} " + "x" * 1000}
            if i % 2 == 0
            else {"role": "assistant", "content": f"reply-{i} " + "x" * 1000}
            for i in range(20)
        ]
        last_msg = msgs[-1]["content"]

        result = preflight_check("test-model", msgs, context_window=3000, max_output_tokens=200)

        # Last message must survive
        assert msgs[-1]["content"] == last_msg
        # Oldest messages should have been dropped
        assert result.compacted is True
        assert len(msgs) < 20


# ---------------------------------------------------------------------------
# _compact_messages
# ---------------------------------------------------------------------------


class TestCompactMessages:
    def test_drops_oldest_first(self):
        msgs = [{"role": "user", "content": f"msg-{i} " + "x" * 500} for i in range(12)]
        dropped = _compact_messages(
            msgs, context_window=1500, max_output_tokens=100, system="", tools=None
        )
        assert dropped > 0
        # First remaining message should NOT be msg-0
        assert "msg-0" not in msgs[0].get("content", "")

    def test_no_compaction_needed(self):
        msgs = [{"role": "user", "content": "hi"}]
        dropped = _compact_messages(
            msgs, context_window=100000, max_output_tokens=100, system="", tools=None
        )
        assert dropped == 0

    def test_all_system_messages(self):
        """If all messages are system messages, nothing is dropped."""
        msgs = [{"role": "system", "content": f"sys-{i}"} for i in range(10)]
        dropped = _compact_messages(
            msgs, context_window=100, max_output_tokens=50, system="", tools=None
        )
        assert dropped == 0
