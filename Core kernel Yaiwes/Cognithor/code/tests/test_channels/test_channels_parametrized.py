"""Cross-channel parametrized test suite.

Tests common behaviors across ALL channel types using @pytest.mark.parametrize.
Each channel is instantiated with mocked dependencies and validated for:
  1. name property returns expected string
  2. Constructor does not crash
  3. send() before start() is graceful (no crash)
  4. Empty/whitespace messages handled gracefully

Channels tested:
  CLI, Telegram, Discord, Slack, WhatsApp, Signal, Matrix, IRC,
  Mattermost, Teams, WebUI
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Channel imports -- wrapped in try/except for optional dependencies
# ---------------------------------------------------------------------------
from cognithor.channels.cli import CliChannel
from cognithor.channels.discord import DiscordChannel
from cognithor.channels.irc import IRCChannel
from cognithor.channels.matrix import MatrixChannel
from cognithor.channels.mattermost import MattermostChannel
from cognithor.channels.signal import SignalChannel
from cognithor.channels.slack import SlackChannel
from cognithor.channels.teams import TeamsChannel
from cognithor.channels.telegram import TelegramChannel
from cognithor.channels.webui import WebUIChannel
from cognithor.channels.whatsapp import WhatsAppChannel
from cognithor.models import OutgoingMessage

# ---------------------------------------------------------------------------
# Factory helpers -- each returns an instantiated channel with mocked deps
# ---------------------------------------------------------------------------


def _make_cli() -> CliChannel:
    ch = CliChannel(version="0.0.0-test")
    ch._console = MagicMock()  # prevent real terminal output
    return ch


def _make_telegram() -> TelegramChannel:
    with patch("cognithor.channels.telegram.get_token_store") as mock_ts:
        store = MagicMock()
        store.retrieve.return_value = "fake-telegram-token"
        mock_ts.return_value = store
        return TelegramChannel(token="fake-token")


def _make_discord() -> DiscordChannel:
    with patch("cognithor.channels.discord.get_token_store") as mock_ts:
        store = MagicMock()
        store.retrieve.return_value = "fake-discord-token"
        mock_ts.return_value = store
        return DiscordChannel(token="fake-token", channel_id=123456)


def _make_slack() -> SlackChannel:
    with patch("cognithor.channels.slack.get_token_store") as mock_ts:
        store = MagicMock()
        store.retrieve.return_value = "xoxb-fake"
        mock_ts.return_value = store
        return SlackChannel(token="xoxb-fake")


def _make_whatsapp() -> WhatsAppChannel:
    with patch("cognithor.channels.whatsapp.get_token_store") as mock_ts:
        store = MagicMock()
        store.retrieve.return_value = "fake-wa-token"
        mock_ts.return_value = store
        # WhatsApp __init__ tries to load faster-whisper; suppress that
        with patch.dict("sys.modules", {"faster_whisper": None}):
            return WhatsAppChannel(
                api_token="fake-wa-token",
                phone_number_id="123456",
            )


def _make_signal() -> SignalChannel:
    return SignalChannel(
        api_url="http://localhost:9999",
        phone_number="+491234567890",
    )


def _make_matrix() -> MatrixChannel:
    with patch("cognithor.channels.matrix.get_token_store") as mock_ts:
        store = MagicMock()
        store.retrieve.return_value = "fake-matrix-token"
        mock_ts.return_value = store
        return MatrixChannel(
            homeserver="https://matrix.example.com",
            user_id="@test:example.com",
            access_token="fake-token",
        )


def _make_irc() -> IRCChannel:
    return IRCChannel(
        server="irc.example.com",
        port=6667,
        nick="TestBot",
        channels=["#test"],
    )


def _make_mattermost() -> MattermostChannel:
    with patch("cognithor.channels.mattermost.get_token_store") as mock_ts:
        store = MagicMock()
        store.retrieve.return_value = "fake-mm-token"
        mock_ts.return_value = store
        return MattermostChannel(
            url="https://mm.example.com",
            token="fake-mm-token",
            default_channel="test-channel-id",
        )


def _make_teams() -> TeamsChannel:
    with patch("cognithor.channels.teams.get_token_store") as mock_ts:
        store = MagicMock()
        store.retrieve.return_value = "fake-teams-pw"
        mock_ts.return_value = store
        return TeamsChannel(
            app_id="fake-app-id",
            app_password="fake-pw",
        )


def _make_webui() -> WebUIChannel:
    with patch("cognithor.channels.webui.get_token_store") as mock_ts:
        store = MagicMock()
        store.retrieve.return_value = "fake-webui-token"
        mock_ts.return_value = store
        return WebUIChannel(
            host="127.0.0.1",
            port=19999,
            static_dir=None,
        )


# ---------------------------------------------------------------------------
# Parametrize data: (factory_func, expected_name)
# ---------------------------------------------------------------------------

CHANNEL_PARAMS = [
    pytest.param(_make_cli, "cli", id="cli"),
    pytest.param(_make_telegram, "telegram", id="telegram"),
    pytest.param(_make_discord, "discord", id="discord"),
    pytest.param(_make_slack, "slack", id="slack"),
    pytest.param(_make_whatsapp, "whatsapp", id="whatsapp"),
    pytest.param(_make_signal, "signal", id="signal"),
    pytest.param(_make_matrix, "matrix", id="matrix"),
    pytest.param(_make_irc, "irc", id="irc"),
    pytest.param(_make_mattermost, "mattermost", id="mattermost"),
    pytest.param(_make_teams, "teams", id="teams"),
    pytest.param(_make_webui, "webui", id="webui"),
]


# ===========================================================================
# Test 1: Constructor doesn't crash
# ===========================================================================


class TestConstructor:
    """Verify that each channel can be instantiated without errors."""

    @pytest.mark.parametrize("factory,expected_name", CHANNEL_PARAMS)
    def test_instantiation_succeeds(self, factory: Any, expected_name: str) -> None:
        channel = factory()
        assert channel is not None


# ===========================================================================
# Test 2: name property returns expected string
# ===========================================================================


class TestNameProperty:
    """Verify the `name` property for every channel."""

    @pytest.mark.parametrize("factory,expected_name", CHANNEL_PARAMS)
    def test_name_returns_expected(self, factory: Any, expected_name: str) -> None:
        channel = factory()
        assert channel.name == expected_name

    @pytest.mark.parametrize("factory,expected_name", CHANNEL_PARAMS)
    def test_name_is_string(self, factory: Any, expected_name: str) -> None:
        channel = factory()
        assert isinstance(channel.name, str)

    @pytest.mark.parametrize("factory,expected_name", CHANNEL_PARAMS)
    def test_name_is_non_empty(self, factory: Any, expected_name: str) -> None:
        channel = factory()
        assert len(channel.name) > 0


# ===========================================================================
# Test 3: send() without prior start() -- should not crash
# ===========================================================================


class TestSendWithoutStart:
    """Calling send() before start() must not raise.

    Channels should handle the missing client/connection gracefully,
    either returning silently or logging a warning.
    """

    @pytest.mark.parametrize("factory,expected_name", CHANNEL_PARAMS)
    async def test_send_before_start_no_crash(self, factory: Any, expected_name: str) -> None:
        channel = factory()
        msg = OutgoingMessage(
            channel=expected_name,
            text="Hello before start",
            session_id="test-session-001",
        )
        # Should not raise -- graceful handling
        await channel.send(msg)


# ===========================================================================
# Test 4: Empty / whitespace messages handled gracefully
# ===========================================================================


class TestEmptyMessages:
    """send() with empty or whitespace-only text must not crash."""

    @pytest.mark.parametrize("factory,expected_name", CHANNEL_PARAMS)
    async def test_send_empty_string(self, factory: Any, expected_name: str) -> None:
        channel = factory()
        msg = OutgoingMessage(
            channel=expected_name,
            text="",
            session_id="test-session-002",
        )
        await channel.send(msg)

    @pytest.mark.parametrize("factory,expected_name", CHANNEL_PARAMS)
    async def test_send_whitespace_only(self, factory: Any, expected_name: str) -> None:
        channel = factory()
        msg = OutgoingMessage(
            channel=expected_name,
            text="   ",
            session_id="test-session-003",
        )
        await channel.send(msg)


# ===========================================================================
# Test 5: stop() without start() -- should not crash
# ===========================================================================


class TestStopWithoutStart:
    """Calling stop() on an un-started channel should be safe."""

    @pytest.mark.parametrize("factory,expected_name", CHANNEL_PARAMS)
    async def test_stop_before_start_no_crash(self, factory: Any, expected_name: str) -> None:
        channel = factory()
        await channel.stop()


# ===========================================================================
# Test 6: send_streaming_token without start() -- should not crash
# ===========================================================================


class TestStreamingTokenWithoutStart:
    """send_streaming_token() before start() must not raise."""

    @pytest.mark.parametrize("factory,expected_name", CHANNEL_PARAMS)
    async def test_streaming_token_before_start(self, factory: Any, expected_name: str) -> None:
        channel = factory()
        await channel.send_streaming_token("test-session-004", "hello")


# ===========================================================================
# Test 7: request_approval without start() -- should return False
# ===========================================================================


class TestApprovalWithoutStart:
    """request_approval() before start() should return False or not crash."""

    @pytest.mark.parametrize("factory,expected_name", CHANNEL_PARAMS)
    async def test_approval_before_start_returns_false(
        self, factory: Any, expected_name: str
    ) -> None:
        from cognithor.models import PlannedAction

        channel = factory()
        action = PlannedAction(tool="test_tool", params={"key": "value"})

        # CLI's request_approval reads from stdin -- mock _read_input
        # to simulate user declining (returns "n").
        if expected_name == "cli":
            channel._read_input = AsyncMock(return_value="n")

        result = await channel.request_approval(
            session_id="test-session-005",
            action=action,
            reason="test reason",
        )
        assert result is False


# ===========================================================================
# Test 8: Channel name uniqueness
# ===========================================================================


class TestChannelNameUniqueness:
    """All channel names should be unique across the set."""

    def test_all_names_unique(self) -> None:
        names = []
        for param in CHANNEL_PARAMS:
            factory = param.values[0]
            channel = factory()
            names.append(channel.name)
        assert len(names) == len(set(names)), f"Duplicate channel names found: {names}"


# ===========================================================================
# Test 9: Channel inherits from Channel base class
# ===========================================================================


class TestInheritance:
    """Every channel must be a subclass of the abstract Channel base."""

    @pytest.mark.parametrize("factory,expected_name", CHANNEL_PARAMS)
    def test_is_channel_subclass(self, factory: Any, expected_name: str) -> None:
        from cognithor.channels.base import Channel

        channel = factory()
        assert isinstance(channel, Channel)
