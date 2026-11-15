"""Tests für das Status-Callback-System.

Testet:
  - StatusType-Enum
  - Base-Channel send_status() (no-op Default)
  - CLI-Channel send_status()
  - Gateway _make_status_callback()
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from cognithor.channels.base import Channel, StatusType


class TestStatusType:
    """Tests für das StatusType-Enum."""

    def test_all_values_exist(self) -> None:
        assert StatusType.THINKING == "thinking"
        assert StatusType.SEARCHING == "searching"
        assert StatusType.EXECUTING == "executing"
        assert StatusType.RETRYING == "retrying"
        assert StatusType.PROCESSING == "processing"
        assert StatusType.FINISHING == "finishing"

    def test_is_str_enum(self) -> None:
        assert isinstance(StatusType.THINKING, str)
        assert StatusType.THINKING == "thinking"


class TestBaseChannelSendStatus:
    """Tests für die Default send_status() Implementierung."""

    @pytest.mark.asyncio
    async def test_default_send_status_is_noop(self) -> None:
        """Base class send_status should be a no-op (no exception)."""

        # Create a concrete implementation for testing
        class TestChannel(Channel):
            @property
            def name(self) -> str:
                return "test"

            async def start(self, handler):
                pass

            async def stop(self):
                pass

            async def send(self, message):
                pass

            async def request_approval(self, session_id, action, reason):
                return True

            async def send_streaming_token(self, session_id, token):
                pass

        channel = TestChannel()
        # Should not raise
        await channel.send_status("session-1", StatusType.THINKING, "Denke nach...")


class TestCliChannelSendStatus:
    """Tests für CLI send_status()."""

    @pytest.mark.asyncio
    async def test_cli_send_status_prints(self) -> None:
        from cognithor.channels.cli import CliChannel

        channel = CliChannel()
        channel._console = MagicMock()

        await channel.send_status("session-1", StatusType.THINKING, "Denke nach...")

        channel._console.print.assert_called_once()
        call_args = channel._console.print.call_args
        assert "Denke nach..." in call_args[0][0]


class TestGatewayStatusCallback:
    """Tests für den Gateway _make_status_callback()."""

    @pytest.mark.asyncio
    async def test_callback_calls_channel_send_status(self) -> None:
        from cognithor.gateway.gateway import Gateway

        gateway = Gateway.__new__(Gateway)
        gateway._channels = {}

        mock_channel = AsyncMock()
        mock_channel.send_status = AsyncMock()
        gateway._channels["test"] = mock_channel

        callback = gateway._make_status_callback("test", "session-1")
        await callback("thinking", "Denke nach...")

        mock_channel.send_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_callback_no_channel_no_error(self) -> None:
        from cognithor.gateway.gateway import Gateway

        gateway = Gateway.__new__(Gateway)
        gateway._channels = {}

        callback = gateway._make_status_callback("nonexistent", "session-1")
        # Should not raise
        await callback("thinking", "Denke nach...")

    @pytest.mark.asyncio
    async def test_callback_handles_exception(self) -> None:
        from cognithor.gateway.gateway import Gateway

        gateway = Gateway.__new__(Gateway)
        gateway._channels = {}

        mock_channel = AsyncMock()
        mock_channel.send_status = AsyncMock(side_effect=Exception("test error"))
        gateway._channels["test"] = mock_channel

        callback = gateway._make_status_callback("test", "session-1")
        # Should not raise even when channel raises
        await callback("thinking", "Denke nach...")


class TestDiscordMessageSplitting:
    """Tests für Discord Message-Splitting."""

    def test_short_message_no_split(self) -> None:
        from cognithor.channels.discord import _split_discord_message

        result = _split_discord_message("Hello")
        assert result == ["Hello"]

    def test_empty_message(self) -> None:
        from cognithor.channels.discord import _split_discord_message

        result = _split_discord_message("")
        assert result == [""]

    def test_long_message_splits(self) -> None:
        from cognithor.channels.discord import _split_discord_message

        text = "A" * 3000
        result = _split_discord_message(text, limit=2000)
        assert len(result) == 2
        assert len(result[0]) <= 2000
        assert "".join(result) == text

    def test_splits_at_newline(self) -> None:
        from cognithor.channels.discord import _split_discord_message

        text = "A" * 1500 + "\n" + "B" * 1500
        result = _split_discord_message(text, limit=2000)
        assert len(result) == 2
        assert result[0] == "A" * 1500

    def test_splits_at_space(self) -> None:
        from cognithor.channels.discord import _split_discord_message

        text = " ".join(["word"] * 500)
        result = _split_discord_message(text, limit=2000)
        assert all(len(c) <= 2000 for c in result)

    def test_three_way_split(self) -> None:
        from cognithor.channels.discord import _split_discord_message

        text = "X" * 5000
        result = _split_discord_message(text, limit=2000)
        assert len(result) == 3


class TestToolStatusMap:
    """Tests für die Tool-Status-Map im Gateway."""

    def test_common_tools_mapped(self) -> None:
        from cognithor.gateway.gateway import _TOOL_STATUS_KEYS

        assert "web_search" in _TOOL_STATUS_KEYS
        assert "exec_command" in _TOOL_STATUS_KEYS
        assert "read_file" in _TOOL_STATUS_KEYS
        assert len(_TOOL_STATUS_KEYS) >= 10

    def test_status_keys_are_i18n_keys(self) -> None:
        from cognithor.gateway.gateway import _TOOL_STATUS_KEYS

        for tool, key in _TOOL_STATUS_KEYS.items():
            assert key.startswith("gateway.status_"), f"{tool}: '{key}'"


class TestExecutorStatusCallback:
    """Tests für Executor set_status_callback."""

    def test_set_status_callback(self) -> None:
        from cognithor.core.executor import Executor

        cfg = MagicMock()
        cfg.executor = None
        ex = Executor(cfg)
        cb = AsyncMock()
        ex.set_status_callback(cb)
        assert ex._status_callback is cb
