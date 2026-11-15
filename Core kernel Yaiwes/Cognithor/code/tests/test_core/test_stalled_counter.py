"""Tests for the formal stalled-turn counter."""

from __future__ import annotations

from cognithor.gateway.gateway import MAX_STALLED_MODEL_TURNS, advance_stalled_count
from cognithor.models import SessionContext

# ── Unit tests for advance_stalled_count ────────────────────────


class TestAdvanceStalledCount:
    """Pure-function tests — no I/O needed."""

    def test_resets_on_successful_tool_calls(self) -> None:
        assert advance_stalled_count(5, tool_calls=2, successful_calls=1) == 0

    def test_resets_when_all_succeed(self) -> None:
        assert advance_stalled_count(19, tool_calls=3, successful_calls=3) == 0

    def test_increments_when_no_tool_calls(self) -> None:
        assert advance_stalled_count(0, tool_calls=0, successful_calls=0) == 1

    def test_increments_when_tools_called_but_none_succeed(self) -> None:
        assert advance_stalled_count(4, tool_calls=3, successful_calls=0) == 5

    def test_increments_from_zero(self) -> None:
        assert advance_stalled_count(0, tool_calls=0, successful_calls=0) == 1

    def test_chain_to_limit(self) -> None:
        """Simulate reaching the stalled limit purely through the counter."""
        count = 0
        for _ in range(MAX_STALLED_MODEL_TURNS):
            count = advance_stalled_count(count, tool_calls=0, successful_calls=0)
        assert count == MAX_STALLED_MODEL_TURNS

    def test_reset_after_long_stall(self) -> None:
        """Even a long stall resets on one successful call."""
        count = 19
        count = advance_stalled_count(count, tool_calls=1, successful_calls=1)
        assert count == 0

    def test_zero_tool_calls_positive_success_still_increments(self) -> None:
        """Edge case: successful_calls > 0 but tool_calls == 0 (shouldn't happen,
        but the function should still increment because no tools were called)."""
        assert advance_stalled_count(3, tool_calls=0, successful_calls=1) == 4


# ── Constant sanity ─────────────────────────────────────────────


def test_max_stalled_turns_is_20() -> None:
    assert MAX_STALLED_MODEL_TURNS == 20


# ── SessionContext field ────────────────────────────────────────


class TestSessionContextStalledField:
    def test_default_is_zero(self) -> None:
        ctx = SessionContext()
        assert ctx.stalled_turn_count == 0

    def test_can_set_and_read(self) -> None:
        ctx = SessionContext(stalled_turn_count=7)
        assert ctx.stalled_turn_count == 7

    def test_mutable_update(self) -> None:
        ctx = SessionContext()
        ctx.stalled_turn_count = 15
        assert ctx.stalled_turn_count == 15


# ── Integration-style: simulate a stall sequence ────────────────


class TestStalledSequenceIntegration:
    def test_full_stall_then_recovery(self) -> None:
        """Simulate 10 failed turns, then a success, then more failures."""
        ctx = SessionContext()

        # 10 stalled turns
        for _ in range(10):
            ctx.stalled_turn_count = advance_stalled_count(
                ctx.stalled_turn_count, tool_calls=0, successful_calls=0
            )
        assert ctx.stalled_turn_count == 10

        # One success resets
        ctx.stalled_turn_count = advance_stalled_count(
            ctx.stalled_turn_count, tool_calls=1, successful_calls=1
        )
        assert ctx.stalled_turn_count == 0

        # 20 more stalled turns → hits limit
        for _ in range(20):
            ctx.stalled_turn_count = advance_stalled_count(
                ctx.stalled_turn_count, tool_calls=0, successful_calls=0
            )
        assert ctx.stalled_turn_count == MAX_STALLED_MODEL_TURNS

    def test_tools_called_but_all_fail_counts_as_stalled(self) -> None:
        ctx = SessionContext()
        for _ in range(5):
            ctx.stalled_turn_count = advance_stalled_count(
                ctx.stalled_turn_count, tool_calls=2, successful_calls=0
            )
        assert ctx.stalled_turn_count == 5
