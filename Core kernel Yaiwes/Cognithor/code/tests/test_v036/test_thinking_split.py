"""Tests for Feature 6: Thinking / Execution Split."""

from __future__ import annotations

import pytest

from cognithor.core.roles import (
    should_log_output,
    uses_extended_thinking,
)


class TestThinkingSplit:
    def test_orchestrator_thinking_not_in_conversation_log(self):
        """Orchestrator thinking should NOT be logged."""
        assert uses_extended_thinking("orchestrator") is True
        assert should_log_output("orchestrator") is False

    def test_worker_has_no_thinking_tokens(self):
        """Worker does not use extended thinking."""
        assert uses_extended_thinking("worker") is False
        assert should_log_output("worker") is True

    def test_monitor_has_no_thinking_tokens(self):
        """Monitor does not use extended thinking."""
        assert uses_extended_thinking("monitor") is False
        assert should_log_output("monitor") is True

    def test_orchestrator_thinking_counted_in_cost(self):
        """Thinking tokens must be counted in cost tracking even if not logged.

        This test verifies the role behaviour dict has the correct flags.
        Actual cost tracking integration tested in telemetry tests.
        """
        from cognithor.core.roles import ROLE_BEHAVIOURS

        orch = ROLE_BEHAVIOURS["orchestrator"]
        # Extended thinking is ON (tokens generated, just not logged)
        assert orch["extended_thinking"] is True
        # Output not logged to conversation
        assert orch["log_output"] is False

    @pytest.mark.parametrize("role", ["orchestrator", "worker", "monitor"])
    def test_thinking_flag_consistent_with_log_flag(self, role):
        """Only orchestrator should have thinking=True AND log=False."""
        from cognithor.core.roles import ROLE_BEHAVIOURS

        b = ROLE_BEHAVIOURS[role]
        if role == "orchestrator":
            assert b["extended_thinking"] is True
            assert b["log_output"] is False
        else:
            assert b["extended_thinking"] is False
            assert b["log_output"] is True
