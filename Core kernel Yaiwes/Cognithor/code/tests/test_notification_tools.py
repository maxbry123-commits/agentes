"""Tests for jarvis.mcp.notification_tools."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cognithor.security.encrypted_db import encrypted_connect

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "reminders.db"


@pytest.fixture
def notification_tools(db_path: Path):
    from cognithor.mcp.notification_tools import NotificationTools

    tools = NotificationTools(db_path)
    yield tools
    tools.shutdown()


@pytest.fixture
def mock_mcp_client() -> MagicMock:
    client = MagicMock()
    client.register_builtin_handler = MagicMock()
    return client


@pytest.fixture
def mock_config(tmp_path: Path) -> MagicMock:
    cfg = MagicMock()
    cfg.cognithor_home = tmp_path / ".cognithor"
    return cfg


# ---------------------------------------------------------------------------
# Database creation & schema
# ---------------------------------------------------------------------------


class TestDatabaseCreation:
    def test_db_created(self, db_path: Path, notification_tools):
        assert db_path.exists()

    def test_schema_has_reminders_table(self, db_path: Path, notification_tools):
        conn = encrypted_connect(str(db_path))
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reminders'")
        assert cur.fetchone() is not None
        conn.close()

    def test_schema_columns(self, db_path: Path, notification_tools):
        conn = encrypted_connect(str(db_path))
        cur = conn.execute("PRAGMA table_info(reminders)")
        columns = {row[1] for row in cur.fetchall()}
        assert columns >= {"id", "text", "created_at", "due_at", "repeat", "status", "fired_at"}
        conn.close()


# ---------------------------------------------------------------------------
# set_reminder
# ---------------------------------------------------------------------------


class TestSetReminder:
    @pytest.mark.asyncio
    async def test_set_with_delay(self, notification_tools):
        result = await notification_tools.set_reminder(text="Test", delay_minutes=60)
        assert "id" in result
        assert result["status"] == "pending"
        assert result["repeat"] == "none"

    @pytest.mark.asyncio
    async def test_set_with_absolute_time(self, notification_tools):
        future = (datetime.now(UTC) + timedelta(hours=2)).isoformat()
        result = await notification_tools.set_reminder(text="Absolute", at=future)
        assert "id" in result
        assert result["text"] == "Absolute"

    @pytest.mark.asyncio
    async def test_set_with_repeat_daily(self, notification_tools):
        result = await notification_tools.set_reminder(
            text="Daily check", delay_minutes=1, repeat="daily"
        )
        assert result["repeat"] == "daily"

    @pytest.mark.asyncio
    async def test_set_with_repeat_weekly(self, notification_tools):
        result = await notification_tools.set_reminder(
            text="Weekly sync", delay_minutes=1, repeat="weekly"
        )
        assert result["repeat"] == "weekly"

    @pytest.mark.asyncio
    async def test_invalid_repeat(self, notification_tools):
        result = await notification_tools.set_reminder(
            text="Bad", delay_minutes=1, repeat="monthly"
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_no_time_specified(self, notification_tools):
        result = await notification_tools.set_reminder(text="No time")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_invalid_iso_datetime(self, notification_tools):
        result = await notification_tools.set_reminder(text="Bad dt", at="not-a-date")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_negative_delay(self, notification_tools):
        result = await notification_tools.set_reminder(text="Neg", delay_minutes=-5)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_max_limit_enforcement(self, notification_tools):
        from cognithor.mcp.notification_tools import _MAX_ACTIVE_REMINDERS

        # Insert max reminders directly into DB
        now = datetime.now(UTC)
        future = (now + timedelta(hours=1)).isoformat()
        for i in range(_MAX_ACTIVE_REMINDERS):
            notification_tools._conn.execute(
                "INSERT INTO reminders (text, created_at, due_at, repeat, status) "
                "VALUES (?, ?, ?, 'none', 'pending')",
                (f"r{i}", now.isoformat(), future),
            )
        notification_tools._conn.commit()

        result = await notification_tools.set_reminder(text="Over limit", delay_minutes=10)
        assert "error" in result
        assert "Maximum" in result["error"]


# ---------------------------------------------------------------------------
# list_reminders
# ---------------------------------------------------------------------------


class TestListReminders:
    @pytest.mark.asyncio
    async def test_empty_list(self, notification_tools):
        result = await notification_tools.list_reminders()
        assert result == []

    @pytest.mark.asyncio
    async def test_list_pending_only(self, notification_tools):
        await notification_tools.set_reminder(text="A", delay_minutes=60)
        result = await notification_tools.list_reminders(include_past=False)
        assert len(result) == 1
        assert result[0]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_list_include_past(self, notification_tools):
        await notification_tools.set_reminder(text="A", delay_minutes=60)
        # Manually mark as fired
        notification_tools._conn.execute("UPDATE reminders SET status = 'fired' WHERE text = 'A'")
        notification_tools._conn.commit()

        pending = await notification_tools.list_reminders(include_past=False)
        assert len(pending) == 0

        all_items = await notification_tools.list_reminders(include_past=True)
        assert len(all_items) == 1
        assert all_items[0]["status"] == "fired"


# ---------------------------------------------------------------------------
# cancel_reminder
# ---------------------------------------------------------------------------


class TestCancelReminder:
    @pytest.mark.asyncio
    async def test_cancel(self, notification_tools):
        r = await notification_tools.set_reminder(text="Cancel me", delay_minutes=60)
        result = await notification_tools.cancel_reminder(r["id"])
        assert result["status"] == "cancelled"

        pending = await notification_tools.list_reminders()
        assert len(pending) == 0


# ---------------------------------------------------------------------------
# Repeat logic
# ---------------------------------------------------------------------------


class TestRepeatLogic:
    @pytest.mark.asyncio
    async def test_fire_creates_next_daily(self, notification_tools):
        with patch(
            "cognithor.mcp.notification_tools._send_desktop_notification",
            new_callable=AsyncMock,
            return_value="ok",
        ):
            r = await notification_tools.set_reminder(
                text="Repeat daily", delay_minutes=0, repeat="daily"
            )
            # Fire it manually
            await notification_tools._fire_reminder(r["id"], "Repeat daily", "daily")

        # Should have original (fired) + new (pending)
        all_items = await notification_tools.list_reminders(include_past=True)
        assert len(all_items) == 2
        statuses = {item["status"] for item in all_items}
        assert "fired" in statuses
        assert "pending" in statuses

    @pytest.mark.asyncio
    async def test_fire_creates_next_weekly(self, notification_tools):
        with patch(
            "cognithor.mcp.notification_tools._send_desktop_notification",
            new_callable=AsyncMock,
            return_value="ok",
        ):
            r = await notification_tools.set_reminder(
                text="Repeat weekly", delay_minutes=0, repeat="weekly"
            )
            await notification_tools._fire_reminder(r["id"], "Repeat weekly", "weekly")

        all_items = await notification_tools.list_reminders(include_past=True)
        pending = [i for i in all_items if i["status"] == "pending"]
        assert len(pending) == 1
        # Next due should be ~7 days out
        due = datetime.fromisoformat(pending[0]["due_at"])
        now = datetime.now(UTC)
        diff = due - now
        assert diff.days >= 6


# ---------------------------------------------------------------------------
# restore_pending
# ---------------------------------------------------------------------------


class TestRestorePending:
    @pytest.mark.asyncio
    async def test_restore_overdue(self, notification_tools):
        """Overdue reminders should fire immediately on restore."""
        past = (datetime.now(UTC) - timedelta(minutes=5)).isoformat()
        notification_tools._conn.execute(
            "INSERT INTO reminders (text, created_at, due_at, repeat, status) "
            "VALUES ('Overdue', ?, ?, 'none', 'pending')",
            (past, past),
        )
        notification_tools._conn.commit()

        with patch(
            "cognithor.mcp.notification_tools._send_desktop_notification",
            new_callable=AsyncMock,
            return_value="ok",
        ):
            count = await notification_tools.restore_pending()

        assert count == 1
        items = await notification_tools.list_reminders(include_past=True)
        assert items[0]["status"] == "fired"

    @pytest.mark.asyncio
    async def test_restore_future(self, notification_tools):
        """Future reminders should be rescheduled."""
        now = datetime.now(UTC)
        future = (now + timedelta(hours=1)).isoformat()
        notification_tools._conn.execute(
            "INSERT INTO reminders (text, created_at, due_at, repeat, status) "
            "VALUES ('Future', ?, ?, 'none', 'pending')",
            (now.isoformat(), future),
        )
        notification_tools._conn.commit()

        count = await notification_tools.restore_pending()
        assert count == 1
        # Should still be pending
        items = await notification_tools.list_reminders()
        assert len(items) == 1
        assert items[0]["status"] == "pending"


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestRegistration:
    def test_register_notification_tools(self, mock_mcp_client, mock_config):
        from cognithor.mcp.notification_tools import register_notification_tools

        tools = register_notification_tools(mock_mcp_client, mock_config)
        assert tools is not None

        # Should register 3 handlers
        assert mock_mcp_client.register_builtin_handler.call_count == 3

        registered_names = [
            call.args[0] for call in mock_mcp_client.register_builtin_handler.call_args_list
        ]
        assert "set_reminder" in registered_names
        assert "list_reminders" in registered_names
        assert "send_notification" in registered_names

    @pytest.mark.asyncio
    async def test_restore_pending_reminders_function(self, mock_mcp_client, mock_config):
        from cognithor.mcp.notification_tools import (
            register_notification_tools,
            restore_pending_reminders,
        )

        tools = register_notification_tools(mock_mcp_client, mock_config)
        # Should not raise even with empty DB
        await restore_pending_reminders(tools)


# ---------------------------------------------------------------------------
# send_notification
# ---------------------------------------------------------------------------


class TestSendNotification:
    @pytest.mark.asyncio
    async def test_send_notification_plyer_fallback(self, notification_tools):
        with patch(
            "cognithor.mcp.notification_tools._try_plyer_notification",
            return_value=True,
        ):
            result = await notification_tools.send_notification(title="Test", message="Hello")
            assert "plyer" in result

    @pytest.mark.asyncio
    async def test_send_notification_all_fallbacks_fail(self, notification_tools):
        with (
            patch("cognithor.mcp.notification_tools._try_plyer_notification", return_value=False),
            patch(
                "cognithor.mcp.notification_tools._try_powershell_notification", return_value=False
            ),
            patch("cognithor.mcp.notification_tools._try_winsound_fallback", return_value=False),
        ):
            result = await notification_tools.send_notification(title="Test", message="Hello")
            assert "logged" in result.lower() or "Notification" in result


# ---------------------------------------------------------------------------
# Shutdown
# ---------------------------------------------------------------------------


class TestShutdown:
    @pytest.mark.asyncio
    async def test_shutdown_cancels_tasks(self, notification_tools):
        await notification_tools.set_reminder(text="Will cancel", delay_minutes=9999)
        assert len(notification_tools._tasks) >= 1
        notification_tools.shutdown()
        assert len(notification_tools._tasks) == 0
