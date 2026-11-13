"""Tests fuer den 3-Tier Context Guard."""

from __future__ import annotations

from cognithor.core.context_guard import (
    COMPACTED_PLACEHOLDER,
    ContextGuardConfig,
    apply_context_guard,
    estimate_messages_tokens,
    truncate_head_tail,
)


class TestTruncateHeadTail:
    def test_short_text_unchanged(self):
        assert truncate_head_tail("hello", 100) == "hello"

    def test_long_text_truncated(self):
        text = "A" * 1000
        result = truncate_head_tail(text, 200)
        assert len(result) <= 200 + 100  # marker overhead
        assert "..." in result or "truncated" in result

    def test_head_preserved(self):
        text = "HEADER" + "x" * 1000 + "FOOTER"
        result = truncate_head_tail(text, 200)
        assert result.startswith("HEADER")

    def test_tail_preserved(self):
        text = "HEADER" + "x" * 1000 + "FOOTER"
        result = truncate_head_tail(text, 200)
        assert result.endswith("FOOTER")


class TestEstimateTokens:
    def test_empty(self):
        assert estimate_messages_tokens([]) == 2

    def test_tool_message_denser(self):
        tool_msg = [{"role": "tool", "content": "x" * 100}]
        user_msg = [{"role": "user", "content": "x" * 100}]
        tool_tokens = estimate_messages_tokens(tool_msg)
        user_tokens = estimate_messages_tokens(user_msg)
        assert tool_tokens > user_tokens  # tool = //2, user = //4


class TestApplyContextGuard:
    def test_disabled_noop(self):
        msgs = [{"role": "tool", "content": "x" * 100000}]
        cfg = ContextGuardConfig(enabled=False)
        result = apply_context_guard(msgs, config=cfg)
        assert result.truncated_tool_results == 0
        assert len(msgs[0]["content"]) == 100000

    def test_tier1_truncation(self):
        # Create a tool result that's >50% of context window
        big_content = "X" * 200_000  # ~100k tokens at //2
        msgs = [
            {"role": "system", "content": "You are helpful."},
            {"role": "tool", "content": big_content},
        ]
        result = apply_context_guard(msgs, context_window_tokens=50_000)
        assert result.truncated_tool_results == 1
        assert len(msgs[1]["content"]) < len(big_content)

    def test_tier2_compaction(self):
        # Many tool results that together exceed 75%
        msgs = [{"role": "system", "content": "sys"}]
        for _i in range(20):
            msgs.append({"role": "tool", "content": "R" * 10_000})
        result = apply_context_guard(msgs, context_window_tokens=20_000)
        assert result.compacted_tool_results > 0
        # Some messages should be replaced with placeholder
        compacted_count = sum(1 for m in msgs if m.get("content") == COMPACTED_PLACEHOLDER)
        assert compacted_count > 0

    def test_tier3_overflow(self):
        # Even after compaction, still over 90%
        msgs = [{"role": "system", "content": "S" * 50_000}]
        for _ in range(10):
            msgs.append({"role": "user", "content": "Q" * 20_000})
        result = apply_context_guard(msgs, context_window_tokens=10_000)
        assert result.tier3_triggered

    def test_small_messages_no_action(self):
        msgs = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hi"},
            {"role": "tool", "content": "Hello there!"},
        ]
        result = apply_context_guard(msgs, context_window_tokens=128_000)
        assert result.truncated_tool_results == 0
        assert result.compacted_tool_results == 0
        assert not result.tier3_triggered
