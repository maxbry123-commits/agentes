"""Extended tests for proactive/__init__.py -- missing lines coverage.

Targets:
  - cleanup_completed edge cases
  - quiet hours over midnight
  - retry logic (retry < max_retries)
  - ProactiveTask duration with invalid dates
  - TaskQueue.get()
  - HeartbeatScheduler.enabled_configs, get_config, trigger_now
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from cognithor.proactive import (
    ApprovalMode,
    EventConfig,
    EventType,
    HeartbeatScheduler,
    ProactiveTask,
    TaskQueue,
    TaskStatus,
)

# ============================================================================
# EventConfig edge cases
# ============================================================================


class TestEventConfigQuietHours:
    def test_quiet_hours_over_midnight(self) -> None:
        """Quiet hours 22-06 (over midnight)."""
        config = EventConfig(
            event_type=EventType.DAILY_BRIEFING,
            quiet_hours_start=22,
            quiet_hours_end=6,
        )
        # Mock hour=23 -> should be in quiet hours
        with patch("cognithor.proactive.datetime") as mock_dt:
            mock_now = datetime(2026, 1, 1, 23, 0, tzinfo=UTC)
            mock_dt.now.return_value = mock_now
            mock_dt.fromisoformat = datetime.fromisoformat
            assert config.is_in_quiet_hours is True

    def test_quiet_hours_over_midnight_early_morning(self) -> None:
        config = EventConfig(
            event_type=EventType.DAILY_BRIEFING,
            quiet_hours_start=22,
            quiet_hours_end=6,
        )
        with patch("cognithor.proactive.datetime") as mock_dt:
            mock_now = datetime(2026, 1, 1, 3, 0, tzinfo=UTC)
            mock_dt.now.return_value = mock_now
            mock_dt.fromisoformat = datetime.fromisoformat
            assert config.is_in_quiet_hours is True

    def test_quiet_hours_normal_range_outside(self) -> None:
        config = EventConfig(
            event_type=EventType.DAILY_BRIEFING,
            quiet_hours_start=22,
            quiet_hours_end=6,
        )
        with patch("cognithor.proactive.datetime") as mock_dt:
            mock_now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
            mock_dt.now.return_value = mock_now
            mock_dt.fromisoformat = datetime.fromisoformat
            assert config.is_in_quiet_hours is False


# ============================================================================
# ProactiveTask edge cases
# ============================================================================


class TestProactiveTaskEdgeCases:
    def test_duration_invalid_dates(self) -> None:
        task = ProactiveTask(
            task_id="t1",
            event_type=EventType.EMAIL_TRIAGE,
            started_at="invalid",
            completed_at="also-invalid",
        )
        assert task.duration_seconds == 0.0

    def test_duration_no_completed_at(self) -> None:
        task = ProactiveTask(
            task_id="t1",
            event_type=EventType.EMAIL_TRIAGE,
            started_at=datetime.now(UTC).isoformat(),
            completed_at="",
        )
        assert task.duration_seconds == 0.0


# ============================================================================
# TaskQueue edge cases
# ============================================================================


class TestTaskQueueEdgeCases:
    def test_get_existing(self) -> None:
        q = TaskQueue()
        task = ProactiveTask(task_id="t1", event_type=EventType.EMAIL_TRIAGE)
        q.enqueue(task)
        assert q.get("t1") is task

    def test_get_nonexistent(self) -> None:
        q = TaskQueue()
        assert q.get("nonexistent") is None

    def test_complete_nonexistent(self) -> None:
        q = TaskQueue()
        assert q.complete("nonexistent") is False

    def test_skip_nonexistent(self) -> None:
        q = TaskQueue()
        assert q.skip("nonexistent") is False

    def test_list_pending(self) -> None:
        q = TaskQueue()
        q.enqueue(ProactiveTask(task_id="t1", event_type=EventType.EMAIL_TRIAGE))
        q.enqueue(ProactiveTask(task_id="t2", event_type=EventType.TODO_REMINDER))
        pending = q.list_pending()
        assert len(pending) == 2

    def test_cleanup_completed_below_keep(self) -> None:
        q = TaskQueue()
        t = ProactiveTask(task_id="t1", event_type=EventType.EMAIL_TRIAGE)
        t.status = TaskStatus.COMPLETED
        t.completed_at = datetime.now(UTC).isoformat()
        q.enqueue(t)
        # keep=100, only 1 completed -> nothing to remove
        removed = q.cleanup_completed(keep=100)
        assert removed == 0

    def test_same_priority_older_first(self) -> None:
        q = TaskQueue()
        old = ProactiveTask(
            task_id="old",
            event_type=EventType.EMAIL_TRIAGE,
            priority=5,
            created_at="2020-01-01T00:00:00Z",
        )
        new = ProactiveTask(
            task_id="new",
            event_type=EventType.EMAIL_TRIAGE,
            priority=5,
            created_at="2026-01-01T00:00:00Z",
        )
        q.enqueue(new)
        q.enqueue(old)
        first = q.dequeue()
        assert first.task_id == "old"


# ============================================================================
# HeartbeatScheduler edge cases
# ============================================================================


class TestHeartbeatSchedulerEdgeCases:
    def test_enabled_configs(self) -> None:
        s = HeartbeatScheduler()
        assert len(s.enabled_configs()) == 0
        s.configure(EventType.EMAIL_TRIAGE, enabled=True)
        assert len(s.enabled_configs()) == 1

    def test_get_config(self) -> None:
        s = HeartbeatScheduler()
        config = s.get_config(EventType.EMAIL_TRIAGE)
        assert config is not None
        assert config.event_type == EventType.EMAIL_TRIAGE

    def test_get_config_custom_returns_none(self) -> None:
        s = HeartbeatScheduler()
        # CUSTOM is not in default configs
        config = s.get_config(EventType.CUSTOM)
        assert config is None

    def test_approve_nonexistent(self) -> None:
        s = HeartbeatScheduler()
        assert s.approve_task("nonexistent") is False

    def test_reject_nonexistent(self) -> None:
        s = HeartbeatScheduler()
        assert s.reject_task("nonexistent") is False

    def test_configure_quiet_hours(self) -> None:
        s = HeartbeatScheduler()
        config = s.configure(
            EventType.EMAIL_TRIAGE,
            quiet_hours=(22, 6),
        )
        assert config.quiet_hours_start == 22
        assert config.quiet_hours_end == 6

    def test_configure_approval_mode(self) -> None:
        s = HeartbeatScheduler()
        config = s.configure(
            EventType.EMAIL_TRIAGE,
            approval_mode=ApprovalMode.SILENT,
        )
        assert config.approval_mode == ApprovalMode.SILENT

    def test_configure_agent_name(self) -> None:
        s = HeartbeatScheduler()
        config = s.configure(
            EventType.EMAIL_TRIAGE,
            agent_name="email_agent",
        )
        assert config.agent_name == "email_agent"

    @pytest.mark.asyncio
    async def test_tick_retry_then_fail(self) -> None:
        s = HeartbeatScheduler()
        s.configure(
            EventType.EMAIL_TRIAGE,
            enabled=True,
            interval_seconds=0,
        )

        call_count = 0

        async def always_fail(task: ProactiveTask) -> str:
            nonlocal call_count
            call_count += 1
            raise RuntimeError("fail")

        s.register_handler(EventType.EMAIL_TRIAGE, always_fail)

        # First tick: handler fails, retry possible (retries=0 < max_retries=2)
        processed = await s.tick()
        assert len(processed) >= 1

    @pytest.mark.asyncio
    async def test_tick_disabled_event_skipped(self) -> None:
        s = HeartbeatScheduler()
        s.configure(EventType.EMAIL_TRIAGE, enabled=False)

        async def handler(task: ProactiveTask) -> str:
            return "done"

        s.register_handler(EventType.EMAIL_TRIAGE, handler)
        processed = await s.tick()
        assert len(processed) == 0

    def test_event_source_access(self) -> None:
        s = HeartbeatScheduler()
        assert s.event_source is not None
