"""Tests for jarvis.mcp.calendar_tools module.

Tests cover:
  - ICS file parsing (manual parser)
  - ICS file creation and appending
  - Event creation
  - Today/upcoming event queries
  - Availability calculation
  - Timezone handling
  - RRULE recurrence parsing
  - Tool registration
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

from cognithor.config import CognithorConfig

if TYPE_CHECKING:
    from pathlib import Path

# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def calendar_config(tmp_path: Path) -> CognithorConfig:
    """CognithorConfig with calendar enabled."""
    ics_path = tmp_path / "test_calendar.ics"
    return CognithorConfig(
        cognithor_home=tmp_path / ".cognithor",
        calendar={
            "enabled": True,
            "ics_path": str(ics_path),
            "timezone": "UTC",
        },
    )


@pytest.fixture
def calendar_config_disabled(tmp_path: Path) -> CognithorConfig:
    """CognithorConfig with calendar disabled."""
    return CognithorConfig(
        cognithor_home=tmp_path / ".cognithor",
    )


@pytest.fixture
def calendar_tools(calendar_config: CognithorConfig):
    """CalendarTools instance."""
    from cognithor.mcp.calendar_tools import CalendarTools

    return CalendarTools(calendar_config)


def _write_ics(path: Path, events_str: str) -> None:
    """Write a complete ICS file with given VEVENT blocks."""
    content = f"BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Test//Test//EN\n{events_str}END:VCALENDAR\n"
    path.write_text(content, encoding="utf-8")


# ── ICS Parsing ────────────────────────────────────────────────────────────


class TestIcsParsing:
    """Tests for manual ICS parser."""

    def test_parse_simple_event(self) -> None:
        from cognithor.mcp.calendar_tools import _parse_ics_manual

        content = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "UID:test-1\n"
            "DTSTART:20240115T100000Z\n"
            "DTEND:20240115T110000Z\n"
            "SUMMARY:Team Meeting\n"
            "LOCATION:Room A\n"
            "DESCRIPTION:Weekly sync\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        events = _parse_ics_manual(content)
        assert len(events) == 1
        ev = events[0]
        assert ev.summary == "Team Meeting"
        assert ev.location == "Room A"
        assert ev.description == "Weekly sync"
        assert ev.uid == "test-1"

    def test_parse_all_day_event(self) -> None:
        from cognithor.mcp.calendar_tools import _parse_ics_manual

        content = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "UID:test-2\n"
            "DTSTART;VALUE=DATE:20240115\n"
            "DTEND;VALUE=DATE:20240116\n"
            "SUMMARY:Holiday\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        events = _parse_ics_manual(content)
        assert len(events) == 1
        assert events[0].all_day is True
        assert events[0].summary == "Holiday"

    def test_parse_multiple_events(self) -> None:
        from cognithor.mcp.calendar_tools import _parse_ics_manual

        content = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "UID:a\n"
            "DTSTART:20240115T100000Z\n"
            "SUMMARY:Event A\n"
            "END:VEVENT\n"
            "BEGIN:VEVENT\n"
            "UID:b\n"
            "DTSTART:20240115T140000Z\n"
            "SUMMARY:Event B\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        events = _parse_ics_manual(content)
        assert len(events) == 2

    def test_parse_empty_content(self) -> None:
        from cognithor.mcp.calendar_tools import _parse_ics_manual

        events = _parse_ics_manual("")
        assert events == []

    def test_parse_event_without_dtstart(self) -> None:
        from cognithor.mcp.calendar_tools import _parse_ics_manual

        content = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "UID:no-start\n"
            "SUMMARY:Bad Event\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        events = _parse_ics_manual(content)
        assert len(events) == 0

    def test_parse_folded_lines(self) -> None:
        from cognithor.mcp.calendar_tools import _parse_ics_manual

        content = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "UID:fold-test\n"
            "DTSTART:20240115T100000Z\n"
            "SUMMARY:This is a very long summ\n"
            " ary that spans two lines\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        events = _parse_ics_manual(content)
        assert len(events) == 1
        assert "long summary" in events[0].summary

    def test_parse_with_tzid(self) -> None:
        from cognithor.mcp.calendar_tools import _parse_ics_manual

        content = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "UID:tz-test\n"
            "DTSTART;TZID=Europe/Berlin:20240115T100000\n"
            "SUMMARY:Berlin Meeting\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        events = _parse_ics_manual(content)
        assert len(events) == 1
        assert events[0].dtstart is not None

    def test_parse_rrule(self) -> None:
        from cognithor.mcp.calendar_tools import _parse_ics_manual

        content = (
            "BEGIN:VCALENDAR\n"
            "BEGIN:VEVENT\n"
            "UID:rrule-test\n"
            "DTSTART:20240115T100000Z\n"
            "DTEND:20240115T110000Z\n"
            "SUMMARY:Weekly Standup\n"
            "RRULE:FREQ=WEEKLY;COUNT=4\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        events = _parse_ics_manual(content)
        assert len(events) == 1
        assert "WEEKLY" in events[0].rrule


# ── ICS Datetime Parsing ──────────────────────────────────────────────────


class TestIcsDatetimeParsing:
    """Tests for _parse_ics_datetime."""

    def test_utc_datetime(self) -> None:
        from cognithor.mcp.calendar_tools import _parse_ics_datetime

        dt = _parse_ics_datetime("20240115T103000Z")
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15
        assert dt.hour == 10
        assert dt.minute == 30
        assert dt.tzinfo == UTC

    def test_local_datetime(self) -> None:
        from cognithor.mcp.calendar_tools import _parse_ics_datetime

        dt = _parse_ics_datetime("20240115T103000")
        assert dt.year == 2024
        assert dt.hour == 10

    def test_date_only(self) -> None:
        from cognithor.mcp.calendar_tools import _parse_ics_datetime

        dt = _parse_ics_datetime("20240115")
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15

    def test_with_tzid_prefix(self) -> None:
        from cognithor.mcp.calendar_tools import _parse_ics_datetime

        dt = _parse_ics_datetime("TZID=Europe/Berlin:20240115T103000")
        assert dt.year == 2024

    def test_invalid_format(self) -> None:
        from cognithor.mcp.calendar_tools import CalendarError, _parse_ics_datetime

        with pytest.raises(CalendarError):
            _parse_ics_datetime("not-a-date")


# ── RRULE Recurrence ──────────────────────────────────────────────────────


class TestRRuleRecurrence:
    """Tests for recurring event generation."""

    def test_daily_recurrence(self) -> None:
        from cognithor.mcp.calendar_tools import _parse_rrule_instances, _VEvent

        event = _VEvent(
            uid="daily",
            summary="Daily Standup",
            dtstart=datetime(2024, 1, 15, 10, 0, tzinfo=UTC),
            dtend=datetime(2024, 1, 15, 10, 30, tzinfo=UTC),
            rrule="FREQ=DAILY;COUNT=5",
        )
        range_start = datetime(2024, 1, 15, 0, 0, tzinfo=UTC)
        range_end = datetime(2024, 1, 25, 23, 59, tzinfo=UTC)

        instances = list(_parse_rrule_instances(event, range_start, range_end))
        assert len(instances) == 5

    def test_weekly_recurrence(self) -> None:
        from cognithor.mcp.calendar_tools import _parse_rrule_instances, _VEvent

        event = _VEvent(
            uid="weekly",
            summary="Weekly Review",
            dtstart=datetime(2024, 1, 15, 14, 0, tzinfo=UTC),
            dtend=datetime(2024, 1, 15, 15, 0, tzinfo=UTC),
            rrule="FREQ=WEEKLY;COUNT=3",
        )
        range_start = datetime(2024, 1, 1, 0, 0, tzinfo=UTC)
        range_end = datetime(2024, 3, 1, 0, 0, tzinfo=UTC)

        instances = list(_parse_rrule_instances(event, range_start, range_end))
        assert len(instances) == 3

    def test_monthly_recurrence(self) -> None:
        from cognithor.mcp.calendar_tools import _parse_rrule_instances, _VEvent

        event = _VEvent(
            uid="monthly",
            summary="Monthly Report",
            dtstart=datetime(2024, 1, 15, 10, 0, tzinfo=UTC),
            dtend=datetime(2024, 1, 15, 11, 0, tzinfo=UTC),
            rrule="FREQ=MONTHLY;COUNT=3",
        )
        range_start = datetime(2024, 1, 1, 0, 0, tzinfo=UTC)
        range_end = datetime(2024, 6, 1, 0, 0, tzinfo=UTC)

        instances = list(_parse_rrule_instances(event, range_start, range_end))
        assert len(instances) == 3

    def test_recurrence_with_until(self) -> None:
        from cognithor.mcp.calendar_tools import _parse_rrule_instances, _VEvent

        event = _VEvent(
            uid="until",
            summary="Limited Event",
            dtstart=datetime(2024, 1, 15, 10, 0, tzinfo=UTC),
            dtend=datetime(2024, 1, 15, 11, 0, tzinfo=UTC),
            rrule="FREQ=DAILY;UNTIL=20240118T235959Z",
        )
        range_start = datetime(2024, 1, 15, 0, 0, tzinfo=UTC)
        range_end = datetime(2024, 1, 31, 0, 0, tzinfo=UTC)

        instances = list(_parse_rrule_instances(event, range_start, range_end))
        assert len(instances) == 4  # 15, 16, 17, 18

    def test_no_rrule_single_event(self) -> None:
        from cognithor.mcp.calendar_tools import _parse_rrule_instances, _VEvent

        event = _VEvent(
            uid="single",
            summary="One-off",
            dtstart=datetime(2024, 1, 15, 10, 0, tzinfo=UTC),
            dtend=datetime(2024, 1, 15, 11, 0, tzinfo=UTC),
        )
        range_start = datetime(2024, 1, 1, 0, 0, tzinfo=UTC)
        range_end = datetime(2024, 2, 1, 0, 0, tzinfo=UTC)

        instances = list(_parse_rrule_instances(event, range_start, range_end))
        assert len(instances) == 1

    def test_recurrence_with_interval(self) -> None:
        from cognithor.mcp.calendar_tools import _parse_rrule_instances, _VEvent

        event = _VEvent(
            uid="bi-weekly",
            summary="Bi-weekly",
            dtstart=datetime(2024, 1, 15, 10, 0, tzinfo=UTC),
            dtend=datetime(2024, 1, 15, 11, 0, tzinfo=UTC),
            rrule="FREQ=WEEKLY;INTERVAL=2;COUNT=3",
        )
        range_start = datetime(2024, 1, 1, 0, 0, tzinfo=UTC)
        range_end = datetime(2024, 4, 1, 0, 0, tzinfo=UTC)

        instances = list(_parse_rrule_instances(event, range_start, range_end))
        assert len(instances) == 3
        # Check 2-week interval
        if len(instances) >= 2:
            delta = instances[1].dtstart - instances[0].dtstart
            assert delta.days == 14


# ── CalendarTools Methods ──────────────────────────────────────────────────


class TestCalendarToday:
    """Tests for calendar_today."""

    async def test_today_no_events(self, calendar_tools: Any) -> None:
        result = await calendar_tools.calendar_today()
        assert "Keine Termine" in result or "no_events" in result or "calendar" in result.lower()

    async def test_today_with_events(self, calendar_tools: Any) -> None:
        now = calendar_tools._now()
        start = now.replace(hour=10, minute=0, second=0, microsecond=0)
        end = now.replace(hour=11, minute=0, second=0, microsecond=0)

        from cognithor.mcp.calendar_tools import _format_ics_datetime

        event_str = (
            "BEGIN:VEVENT\n"
            f"UID:today-test\n"
            f"DTSTART:{_format_ics_datetime(start)}\n"
            f"DTEND:{_format_ics_datetime(end)}\n"
            f"SUMMARY:Today Meeting\n"
            "END:VEVENT\n"
        )
        _write_ics(calendar_tools._ics_path, event_str)

        result = await calendar_tools.calendar_today()
        assert "Today Meeting" in result

    async def test_today_with_specific_date(self, calendar_tools: Any) -> None:
        event_str = (
            "BEGIN:VEVENT\n"
            "UID:specific-date\n"
            "DTSTART:20240115T100000Z\n"
            "DTEND:20240115T110000Z\n"
            "SUMMARY:Jan 15 Event\n"
            "END:VEVENT\n"
        )
        _write_ics(calendar_tools._ics_path, event_str)

        result = await calendar_tools.calendar_today(date="2024-01-15")
        assert "Jan 15 Event" in result

    async def test_today_invalid_date(self, calendar_tools: Any) -> None:
        from cognithor.mcp.calendar_tools import CalendarError

        with pytest.raises(CalendarError, match="Ungültiges Datum"):
            await calendar_tools.calendar_today(date="not-a-date")


class TestCalendarUpcoming:
    """Tests for calendar_upcoming."""

    async def test_upcoming_no_events(self, calendar_tools: Any) -> None:
        result = await calendar_tools.calendar_upcoming(days=7)
        assert "Keine Termine" in result or "no_events" in result or "calendar" in result.lower()

    async def test_upcoming_with_events(self, calendar_tools: Any) -> None:
        now = calendar_tools._now()
        tomorrow = now + timedelta(days=1)
        start = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        end = tomorrow.replace(hour=15, minute=0, second=0, microsecond=0)

        from cognithor.mcp.calendar_tools import _format_ics_datetime

        event_str = (
            "BEGIN:VEVENT\n"
            f"UID:upcoming-test\n"
            f"DTSTART:{_format_ics_datetime(start)}\n"
            f"DTEND:{_format_ics_datetime(end)}\n"
            f"SUMMARY:Tomorrow Meeting\n"
            "END:VEVENT\n"
        )
        _write_ics(calendar_tools._ics_path, event_str)

        result = await calendar_tools.calendar_upcoming(days=7)
        assert "Tomorrow Meeting" in result

    async def test_upcoming_days_clamped(self, calendar_tools: Any) -> None:
        """Days parameter is clamped to 1-90."""
        result = await calendar_tools.calendar_upcoming(days=200)
        # Should not raise, just clamp to 90
        assert (
            "Keine Termine" in result
            or "Termine" in result
            or "no_events" in result
            or "calendar" in result.lower()
        )


class TestCalendarCreateEvent:
    """Tests for calendar_create_event."""

    async def test_create_basic_event(self, calendar_tools: Any) -> None:
        result = await calendar_tools.calendar_create_event(
            title="New Meeting",
            start="2024-06-15T10:00:00",
        )
        assert "Termin erstellt" in result
        assert "New Meeting" in result

        # Verify ICS file updated
        content = calendar_tools._ics_path.read_text(encoding="utf-8")
        assert "New Meeting" in content
        assert "BEGIN:VEVENT" in content

    async def test_create_event_with_end(self, calendar_tools: Any) -> None:
        result = await calendar_tools.calendar_create_event(
            title="Workshop",
            start="2024-06-15T09:00:00",
            end="2024-06-15T17:00:00",
        )
        assert "Termin erstellt" in result

    async def test_create_all_day_event(self, calendar_tools: Any) -> None:
        result = await calendar_tools.calendar_create_event(
            title="Holiday",
            start="2024-12-25",
            all_day=True,
        )
        assert "Termin erstellt" in result

        content = calendar_tools._ics_path.read_text(encoding="utf-8")
        assert "VALUE=DATE" in content

    async def test_create_event_with_location(self, calendar_tools: Any) -> None:
        result = await calendar_tools.calendar_create_event(
            title="Offsite",
            start="2024-06-15T10:00:00",
            location="Conference Room B",
        )
        assert "Ort: Conference Room B" in result

    async def test_create_event_missing_title(self, calendar_tools: Any) -> None:
        from cognithor.mcp.calendar_tools import CalendarError

        with pytest.raises(CalendarError, match="Titel"):
            await calendar_tools.calendar_create_event(title="", start="2024-06-15T10:00:00")

    async def test_create_event_missing_start(self, calendar_tools: Any) -> None:
        from cognithor.mcp.calendar_tools import CalendarError

        with pytest.raises(CalendarError, match="Startzeit"):
            await calendar_tools.calendar_create_event(title="Test", start="")

    async def test_create_event_invalid_start(self, calendar_tools: Any) -> None:
        from cognithor.mcp.calendar_tools import CalendarError

        with pytest.raises(CalendarError, match="Ungültige Startzeit"):
            await calendar_tools.calendar_create_event(title="Test", start="not-a-date")

    async def test_create_event_invalid_end(self, calendar_tools: Any) -> None:
        from cognithor.mcp.calendar_tools import CalendarError

        with pytest.raises(CalendarError, match="Ungültige Endzeit"):
            await calendar_tools.calendar_create_event(
                title="Test", start="2024-06-15T10:00:00", end="bad"
            )

    async def test_create_multiple_events(self, calendar_tools: Any) -> None:
        """Multiple events can be added to the same ICS file."""
        await calendar_tools.calendar_create_event(title="Event 1", start="2024-06-15T10:00:00")
        await calendar_tools.calendar_create_event(title="Event 2", start="2024-06-15T14:00:00")

        content = calendar_tools._ics_path.read_text(encoding="utf-8")
        assert content.count("BEGIN:VEVENT") == 2
        assert "Event 1" in content
        assert "Event 2" in content


class TestCalendarAvailability:
    """Tests for calendar_check_availability."""

    async def test_availability_no_events(self, calendar_tools: Any) -> None:
        now = calendar_tools._now()
        date_str = now.strftime("%Y-%m-%d")
        result = await calendar_tools.calendar_check_availability(date=date_str)
        assert "Freie Zeitfenster" in result

    async def test_availability_with_meeting(self, calendar_tools: Any) -> None:
        now = calendar_tools._now()
        day = now.replace(hour=10, minute=0, second=0, microsecond=0)

        from cognithor.mcp.calendar_tools import _format_ics_datetime

        start = day
        end = day.replace(hour=12)

        event_str = (
            "BEGIN:VEVENT\n"
            f"UID:avail-test\n"
            f"DTSTART:{_format_ics_datetime(start)}\n"
            f"DTEND:{_format_ics_datetime(end)}\n"
            f"SUMMARY:Long Meeting\n"
            "END:VEVENT\n"
        )
        _write_ics(calendar_tools._ics_path, event_str)

        date_str = now.strftime("%Y-%m-%d")
        result = await calendar_tools.calendar_check_availability(
            date=date_str,
            duration_minutes=60,
            work_hours_start="09:00",
            work_hours_end="17:00",
        )
        assert "Freie Zeitfenster" in result or "Belegte" in result

    async def test_availability_fully_booked(self, calendar_tools: Any) -> None:
        now = calendar_tools._now()
        day_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
        day_end = now.replace(hour=17, minute=0, second=0, microsecond=0)

        from cognithor.mcp.calendar_tools import _format_ics_datetime

        event_str = (
            "BEGIN:VEVENT\n"
            f"UID:full-day\n"
            f"DTSTART:{_format_ics_datetime(day_start)}\n"
            f"DTEND:{_format_ics_datetime(day_end)}\n"
            f"SUMMARY:All Day Meeting\n"
            "END:VEVENT\n"
        )
        _write_ics(calendar_tools._ics_path, event_str)

        date_str = now.strftime("%Y-%m-%d")
        result = await calendar_tools.calendar_check_availability(
            date=date_str,
            duration_minutes=60,
        )
        assert (
            "Keine freien" in result
            or "Belegte" in result
            or "no_free" in result
            or "no.*slot" in result.lower()
        )

    async def test_availability_invalid_date(self, calendar_tools: Any) -> None:
        from cognithor.mcp.calendar_tools import CalendarError

        with pytest.raises(CalendarError, match="Ungültiges Datum"):
            await calendar_tools.calendar_check_availability(date="bad")

    async def test_availability_invalid_work_hours(self, calendar_tools: Any) -> None:
        from cognithor.mcp.calendar_tools import CalendarError

        now = calendar_tools._now()
        date_str = now.strftime("%Y-%m-%d")
        with pytest.raises(CalendarError, match="Ungültige Arbeitszeit"):
            await calendar_tools.calendar_check_availability(
                date=date_str,
                work_hours_start="bad",
                work_hours_end="17:00",
            )

    async def test_availability_end_before_start(self, calendar_tools: Any) -> None:
        from cognithor.mcp.calendar_tools import CalendarError

        now = calendar_tools._now()
        date_str = now.strftime("%Y-%m-%d")
        with pytest.raises(CalendarError, match="nach dem Start"):
            await calendar_tools.calendar_check_availability(
                date=date_str,
                work_hours_start="17:00",
                work_hours_end="09:00",
            )


# ── ICS File Management ───────────────────────────────────────────────────


class TestIcsFileManagement:
    """Tests for ICS file creation and management."""

    def test_ics_file_created_on_init(self, calendar_config: CognithorConfig) -> None:
        from cognithor.mcp.calendar_tools import CalendarTools

        tools = CalendarTools(calendar_config)
        assert tools._ics_path.exists()
        content = tools._ics_path.read_text(encoding="utf-8")
        assert "BEGIN:VCALENDAR" in content
        assert "END:VCALENDAR" in content

    def test_read_events_empty_file(self, calendar_tools: Any) -> None:
        events = calendar_tools._read_events()
        assert events == []

    def test_append_event(self, calendar_tools: Any) -> None:
        from cognithor.mcp.calendar_tools import _VEvent

        event = _VEvent(
            uid="append-test",
            summary="Appended Event",
            dtstart=datetime(2024, 6, 15, 10, 0, tzinfo=UTC),
            dtend=datetime(2024, 6, 15, 11, 0, tzinfo=UTC),
        )
        calendar_tools._append_event(event)

        content = calendar_tools._ics_path.read_text(encoding="utf-8")
        assert "Appended Event" in content
        assert "append-test" in content

    def test_append_preserves_existing(self, calendar_tools: Any) -> None:
        from cognithor.mcp.calendar_tools import _VEvent

        event1 = _VEvent(
            uid="first",
            summary="First",
            dtstart=datetime(2024, 6, 15, 10, 0, tzinfo=UTC),
            dtend=datetime(2024, 6, 15, 11, 0, tzinfo=UTC),
        )
        event2 = _VEvent(
            uid="second",
            summary="Second",
            dtstart=datetime(2024, 6, 16, 10, 0, tzinfo=UTC),
            dtend=datetime(2024, 6, 16, 11, 0, tzinfo=UTC),
        )
        calendar_tools._append_event(event1)
        calendar_tools._append_event(event2)

        content = calendar_tools._ics_path.read_text(encoding="utf-8")
        assert "First" in content
        assert "Second" in content
        assert content.count("BEGIN:VEVENT") == 2


# ── VEvent to ICS ─────────────────────────────────────────────────────────


class TestVEventToIcs:
    """Tests for VEvent.to_ics_block."""

    def test_basic_event_block(self) -> None:
        from cognithor.mcp.calendar_tools import _VEvent

        event = _VEvent(
            uid="block-test",
            summary="Test Event",
            dtstart=datetime(2024, 6, 15, 10, 0, tzinfo=UTC),
            dtend=datetime(2024, 6, 15, 11, 0, tzinfo=UTC),
        )
        block = event.to_ics_block()
        assert "BEGIN:VEVENT" in block
        assert "END:VEVENT" in block
        assert "UID:block-test" in block
        assert "SUMMARY:Test Event" in block

    def test_all_day_event_block(self) -> None:
        from cognithor.mcp.calendar_tools import _VEvent

        event = _VEvent(
            uid="allday-block",
            summary="Holiday",
            dtstart=datetime(2024, 12, 25, 0, 0, tzinfo=UTC),
            all_day=True,
        )
        block = event.to_ics_block()
        assert "VALUE=DATE" in block

    def test_event_with_description(self) -> None:
        from cognithor.mcp.calendar_tools import _VEvent

        event = _VEvent(
            uid="desc-test",
            summary="Described",
            dtstart=datetime(2024, 6, 15, 10, 0, tzinfo=UTC),
            description="Line 1\nLine 2",
        )
        block = event.to_ics_block()
        assert "DESCRIPTION:" in block
        assert "\\n" in block  # Escaped newline

    def test_event_to_dict(self) -> None:
        from cognithor.mcp.calendar_tools import _VEvent

        event = _VEvent(
            uid="dict-test",
            summary="Dict Event",
            dtstart=datetime(2024, 6, 15, 10, 0, tzinfo=UTC),
            dtend=datetime(2024, 6, 15, 11, 0, tzinfo=UTC),
            location="Room A",
        )
        d = event.to_dict()
        assert d["title"] == "Dict Event"
        assert d["location"] == "Room A"
        assert d["all_day"] is False


# ── Timezone Handling ──────────────────────────────────────────────────────


class TestTimezoneHandling:
    """Tests for timezone configuration and handling."""

    def test_utc_timezone(self) -> None:
        from cognithor.mcp.calendar_tools import _get_configured_timezone

        tz = _get_configured_timezone("UTC")
        assert tz == UTC or tz.utcoffset(None) == timedelta(0)

    def test_empty_timezone_returns_local(self) -> None:
        from cognithor.mcp.calendar_tools import _get_configured_timezone

        tz = _get_configured_timezone("")
        assert tz is not None  # Should return system timezone

    def test_utc_offset_format(self) -> None:
        from cognithor.mcp.calendar_tools import _get_configured_timezone

        tz = _get_configured_timezone("UTC+2")
        assert tz.utcoffset(None) == timedelta(hours=2)

    def test_utc_negative_offset(self) -> None:
        from cognithor.mcp.calendar_tools import _get_configured_timezone

        tz = _get_configured_timezone("UTC-5")
        assert tz.utcoffset(None) == timedelta(hours=-5)


# ── Tool Registration ──────────────────────────────────────────────────────


class TestRegistration:
    """Tests for register_calendar_tools."""

    def test_register_when_enabled(self, calendar_config: CognithorConfig) -> None:
        from cognithor.mcp.calendar_tools import register_calendar_tools

        mcp = MagicMock()
        result = register_calendar_tools(mcp, calendar_config)
        assert result is not None
        assert mcp.register_builtin_handler.call_count == 4

    def test_register_when_disabled(self, calendar_config_disabled: CognithorConfig) -> None:
        from cognithor.mcp.calendar_tools import register_calendar_tools

        mcp = MagicMock()
        result = register_calendar_tools(mcp, calendar_config_disabled)
        assert result is None
        assert mcp.register_builtin_handler.call_count == 0

    def test_registered_tool_names(self, calendar_config: CognithorConfig) -> None:
        from cognithor.mcp.calendar_tools import register_calendar_tools

        mcp = MagicMock()
        register_calendar_tools(mcp, calendar_config)

        registered_names = [call[0][0] for call in mcp.register_builtin_handler.call_args_list]
        assert "calendar_today" in registered_names
        assert "calendar_upcoming" in registered_names
        assert "calendar_create_event" in registered_names
        assert "calendar_check_availability" in registered_names

    def test_register_creates_ics_file(self, calendar_config: CognithorConfig) -> None:
        from cognithor.mcp.calendar_tools import register_calendar_tools

        mcp = MagicMock()
        result = register_calendar_tools(mcp, calendar_config)
        assert result is not None
        assert result._ics_path.exists()
