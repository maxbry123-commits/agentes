"""Tests for post-execution pattern documentation in Gateway.

Tests:
  - Pattern extraction from successful executions
  - Deduplication (similar pattern skipped)
  - Rate limiting (max 5 per hour)
  - Failure cases not recorded
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock

from cognithor.gateway.gateway import Gateway
from cognithor.models import AgentResult, Message, MessageRole, ToolResult, WorkingMemory

# ── Helpers ──────────────────────────────────────────────────────


def _make_tool_result(tool_name: str, is_error: bool = False) -> ToolResult:
    tr = MagicMock(spec=ToolResult)
    tr.tool_name = tool_name
    tr.is_error = is_error
    tr.content = "result content"
    tr.error_type = "SomeError" if is_error else ""
    return tr


def _make_agent_result(
    success: bool = True,
    tool_results: list | None = None,
) -> AgentResult:
    ar = MagicMock(spec=AgentResult)
    ar.success = success
    ar.tool_results = tool_results or []
    ar.response = "Done"
    ar.total_duration_ms = 100
    ar.reflection = None
    ar.model_used = ""
    ar.error = ""
    return ar


def _make_session(channel: str = "cli") -> MagicMock:
    session = MagicMock()
    session.session_id = "test-session-123"
    session.channel = channel
    return session


def _make_wm_with_user_message(text: str) -> WorkingMemory:
    wm = WorkingMemory()
    wm.add_message(Message(role=MessageRole.USER, content=text))
    return wm


# ── Tests ────────────────────────────────────────────────────────


class TestPatternExtraction:
    """Successful executions get patterns recorded."""

    def test_successful_execution_records_pattern(self) -> None:
        gw = Gateway.__new__(Gateway)
        gw._memory_manager = MagicMock()
        procedural = MagicMock()
        procedural.search_procedures.return_value = ""
        gw._memory_manager.procedural = procedural
        # Reset rate limiter
        Gateway._pattern_record_timestamps = []

        session = _make_session()
        wm = _make_wm_with_user_message("Search for Python tutorials online")
        agent_result = _make_agent_result(
            success=True,
            tool_results=[
                _make_tool_result("web_search"),
                _make_tool_result("search_and_read"),
            ],
        )

        gw._maybe_record_pattern(session, wm, agent_result)

        procedural.save_procedure.assert_called_once()
        call_kwargs = procedural.save_procedure.call_args
        body = call_kwargs[1]["body"] if "body" in (call_kwargs[1] or {}) else call_kwargs[0][1]
        assert "web_search" in body
        assert "search_and_read" in body

    def test_failed_execution_not_recorded(self) -> None:
        gw = Gateway.__new__(Gateway)
        gw._memory_manager = MagicMock()
        procedural = MagicMock()
        gw._memory_manager.procedural = procedural
        Gateway._pattern_record_timestamps = []

        session = _make_session()
        wm = _make_wm_with_user_message("Do something complex")
        agent_result = _make_agent_result(success=False, tool_results=[])

        gw._maybe_record_pattern(session, wm, agent_result)

        procedural.save_procedure.assert_not_called()

    def test_error_in_tools_not_recorded(self) -> None:
        gw = Gateway.__new__(Gateway)
        gw._memory_manager = MagicMock()
        procedural = MagicMock()
        gw._memory_manager.procedural = procedural
        Gateway._pattern_record_timestamps = []

        session = _make_session()
        wm = _make_wm_with_user_message("Try to read a protected file")
        agent_result = _make_agent_result(
            success=True,
            tool_results=[_make_tool_result("read_file", is_error=True)],
        )

        gw._maybe_record_pattern(session, wm, agent_result)

        procedural.save_procedure.assert_not_called()

    def test_no_tools_not_recorded(self) -> None:
        gw = Gateway.__new__(Gateway)
        gw._memory_manager = MagicMock()
        procedural = MagicMock()
        gw._memory_manager.procedural = procedural
        Gateway._pattern_record_timestamps = []

        session = _make_session()
        wm = _make_wm_with_user_message("Just a simple greeting")
        agent_result = _make_agent_result(success=True, tool_results=[])

        gw._maybe_record_pattern(session, wm, agent_result)

        procedural.save_procedure.assert_not_called()


class TestDeduplication:
    """Similar existing patterns are not re-recorded."""

    def test_existing_pattern_skipped(self) -> None:
        gw = Gateway.__new__(Gateway)
        gw._memory_manager = MagicMock()
        procedural = MagicMock()
        # search_procedures returns something containing the tool sequence
        procedural.search_procedures.return_value = "web_search, search_and_read"
        gw._memory_manager.procedural = procedural
        Gateway._pattern_record_timestamps = []

        session = _make_session()
        wm = _make_wm_with_user_message("Search for Python tutorials online")
        agent_result = _make_agent_result(
            success=True,
            tool_results=[
                _make_tool_result("web_search"),
                _make_tool_result("search_and_read"),
            ],
        )

        gw._maybe_record_pattern(session, wm, agent_result)

        procedural.save_procedure.assert_not_called()


class TestRateLimiting:
    """Max 5 pattern recordings per hour."""

    def test_rate_limit_blocks_after_5(self) -> None:
        gw = Gateway.__new__(Gateway)
        gw._memory_manager = MagicMock()
        procedural = MagicMock()
        procedural.search_procedures.return_value = ""
        gw._memory_manager.procedural = procedural

        # Fill rate limiter with 5 recent timestamps
        now = time.monotonic()
        Gateway._pattern_record_timestamps = [now - i for i in range(5)]

        session = _make_session()
        wm = _make_wm_with_user_message("Search for something interesting to read")
        agent_result = _make_agent_result(
            success=True,
            tool_results=[_make_tool_result("web_search")],
        )

        gw._maybe_record_pattern(session, wm, agent_result)

        # Should be blocked by rate limit
        procedural.save_procedure.assert_not_called()

    def test_old_timestamps_pruned(self) -> None:
        gw = Gateway.__new__(Gateway)
        gw._memory_manager = MagicMock()
        procedural = MagicMock()
        procedural.search_procedures.return_value = ""
        gw._memory_manager.procedural = procedural

        # All timestamps are old (> 1 hour ago)
        now = time.monotonic()
        Gateway._pattern_record_timestamps = [now - 7200 for _ in range(5)]

        session = _make_session()
        wm = _make_wm_with_user_message("Search for something interesting to read")
        agent_result = _make_agent_result(
            success=True,
            tool_results=[_make_tool_result("web_search")],
        )

        gw._maybe_record_pattern(session, wm, agent_result)

        # Old timestamps pruned, recording should succeed
        procedural.save_procedure.assert_called_once()

    def test_no_memory_manager_graceful(self) -> None:
        gw = Gateway.__new__(Gateway)
        gw._memory_manager = None
        Gateway._pattern_record_timestamps = []

        session = _make_session()
        wm = _make_wm_with_user_message("Something")
        agent_result = _make_agent_result(success=True)

        # Should not raise
        gw._maybe_record_pattern(session, wm, agent_result)
