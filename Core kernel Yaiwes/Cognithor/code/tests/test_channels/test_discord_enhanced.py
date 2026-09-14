"""Enhanced tests for DiscordChannel -- additional coverage.

Covers: _on_message edge cases, _on_reaction, send methods (send_rich, send_card,
send_progress), request_approval, send_streaming_token, stop lifecycle, start.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cognithor.channels.discord import DiscordChannel
from cognithor.models import OutgoingMessage, PlannedAction


@pytest.fixture
def ch() -> DiscordChannel:
    return DiscordChannel(token="test-token", channel_id=12345)


class TestDiscordProperties:
    def test_name(self, ch: DiscordChannel) -> None:
        assert ch.name == "discord"

    def test_token(self, ch: DiscordChannel) -> None:
        assert ch.token == "test-token"

    def test_is_bidirectional(self, ch: DiscordChannel) -> None:
        assert ch.is_bidirectional is False

    def test_initial_state(self, ch: DiscordChannel) -> None:
        assert ch._running is False
        assert ch._client is None


class TestDiscordOnMessage:
    @pytest.mark.asyncio
    async def test_ignore_own_messages(self, ch: DiscordChannel) -> None:
        ch._client = MagicMock()
        ch._client.user = MagicMock()
        ch._handler = AsyncMock()

        msg = MagicMock()
        msg.author = ch._client.user  # same as bot
        await ch._on_message(msg)
        ch._handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_ignore_bot_messages(self, ch: DiscordChannel) -> None:
        ch._client = MagicMock()
        ch._client.user = MagicMock()
        ch._handler = AsyncMock()

        msg = MagicMock()
        msg.author = MagicMock()
        msg.author.bot = True
        await ch._on_message(msg)
        ch._handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_ignore_empty_text(self, ch: DiscordChannel) -> None:
        ch._client = MagicMock()
        ch._client.user = MagicMock()
        ch._handler = AsyncMock()

        msg = MagicMock()
        msg.author = MagicMock()
        msg.author.bot = False
        msg.content = "   "
        await ch._on_message(msg)
        ch._handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_ignore_irrelevant_channel(self, ch: DiscordChannel) -> None:
        ch._client = MagicMock()
        ch._client.user = MagicMock()
        ch._client.user.id = 999
        ch._handler = AsyncMock()

        msg = MagicMock()
        msg.author = MagicMock()
        msg.author.bot = False
        msg.content = "hello"
        msg.guild = MagicMock()  # not DM
        msg.channel.id = 99999  # wrong channel
        msg.mentions = []
        await ch._on_message(msg)
        ch._handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_accept_dm(self, ch: DiscordChannel) -> None:
        ch._client = MagicMock()
        ch._client.user = MagicMock()
        ch._client.user.id = 999
        response = OutgoingMessage(channel="discord", text="OK")
        ch._handler = AsyncMock(return_value=response)

        msg = MagicMock()
        msg.author = MagicMock()
        msg.author.bot = False
        msg.author.id = 123
        msg.content = "hello"
        msg.guild = None  # DM
        msg.channel = MagicMock()
        msg.channel.id = 555
        msg.channel.send = AsyncMock()
        msg.id = 1
        msg.mentions = []

        await ch._on_message(msg)
        ch._handler.assert_called_once()
        msg.channel.send.assert_called_once_with("OK")

    @pytest.mark.asyncio
    async def test_accept_target_channel(self, ch: DiscordChannel) -> None:
        ch._client = MagicMock()
        ch._client.user = MagicMock()
        ch._client.user.id = 999
        response = OutgoingMessage(channel="discord", text="Response")
        ch._handler = AsyncMock(return_value=response)

        msg = MagicMock()
        msg.author = MagicMock()
        msg.author.bot = False
        msg.author.id = 123
        msg.content = "test"
        msg.guild = MagicMock()
        msg.guild.id = 1
        msg.channel = MagicMock()
        msg.channel.id = 12345  # matches ch.channel_id
        msg.channel.send = AsyncMock()
        msg.id = 1
        msg.mentions = []

        await ch._on_message(msg)
        ch._handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_mention_removes_prefix(self, ch: DiscordChannel) -> None:
        ch._client = MagicMock()
        ch._client.user = MagicMock()
        ch._client.user.id = 999
        response = OutgoingMessage(channel="discord", text="OK")
        ch._handler = AsyncMock(return_value=response)

        msg = MagicMock()
        msg.author = MagicMock()
        msg.author.bot = False
        msg.author.id = 123
        msg.content = "<@999> what is the weather"
        msg.guild = MagicMock()
        msg.guild.id = 1
        msg.channel = MagicMock()
        msg.channel.id = 12345
        msg.channel.send = AsyncMock()
        msg.id = 1
        msg.mentions = [ch._client.user]

        await ch._on_message(msg)
        incoming = ch._handler.call_args[0][0]
        assert incoming.text == "what is the weather"

    @pytest.mark.asyncio
    async def test_handler_response_send_error(self, ch: DiscordChannel) -> None:
        ch._client = MagicMock()
        ch._client.user = MagicMock()
        ch._client.user.id = 999
        response = OutgoingMessage(channel="discord", text="OK")
        ch._handler = AsyncMock(return_value=response)

        msg = MagicMock()
        msg.author = MagicMock()
        msg.author.bot = False
        msg.author.id = 123
        msg.content = "test"
        msg.guild = None
        msg.channel = MagicMock()
        msg.channel.id = 555
        msg.channel.send = AsyncMock(side_effect=RuntimeError("send failed"))
        msg.id = 1
        msg.mentions = []

        # Should log error but not crash
        await ch._on_message(msg)


class TestDiscordOnReaction:
    @pytest.mark.asyncio
    async def test_ignore_own_reaction(self, ch: DiscordChannel) -> None:
        ch._client = MagicMock()
        ch._client.user = MagicMock()

        reaction = MagicMock()
        user = ch._client.user
        await ch._on_reaction(reaction, user)

    @pytest.mark.asyncio
    async def test_approve_reaction(self, ch: DiscordChannel) -> None:
        ch._client = MagicMock()
        ch._client.user = MagicMock()

        future = asyncio.get_event_loop().create_future()
        ch._approval_messages[42] = (future, 123)

        reaction = MagicMock()
        reaction.message.id = 42
        reaction.emoji = "✅"
        user = MagicMock()
        user.id = 123

        await ch._on_reaction(reaction, user)
        assert future.result() is True

    @pytest.mark.asyncio
    async def test_deny_reaction(self, ch: DiscordChannel) -> None:
        ch._client = MagicMock()
        ch._client.user = MagicMock()

        future = asyncio.get_event_loop().create_future()
        ch._approval_messages[42] = (future, 123)

        reaction = MagicMock()
        reaction.message.id = 42
        reaction.emoji = "❌"
        user = MagicMock()
        user.id = 123

        await ch._on_reaction(reaction, user)
        assert future.result() is False

    @pytest.mark.asyncio
    async def test_wrong_user_ignored(self, ch: DiscordChannel) -> None:
        ch._client = MagicMock()
        ch._client.user = MagicMock()

        future = asyncio.get_event_loop().create_future()
        ch._approval_messages[42] = (future, 123)

        reaction = MagicMock()
        reaction.message.id = 42
        reaction.emoji = "✅"
        user = MagicMock()
        user.id = 999  # wrong user

        await ch._on_reaction(reaction, user)
        assert not future.done()

    @pytest.mark.asyncio
    async def test_no_approval_message(self, ch: DiscordChannel) -> None:
        ch._client = MagicMock()
        ch._client.user = MagicMock()

        reaction = MagicMock()
        reaction.message.id = 999
        reaction.emoji = "✅"
        user = MagicMock()
        user.id = 123

        await ch._on_reaction(reaction, user)  # no crash


class TestDiscordSend:
    @pytest.mark.asyncio
    async def test_send_not_running(self, ch: DiscordChannel) -> None:
        ch._running = False
        msg = OutgoingMessage(channel="discord", text="test")
        await ch.send(msg)  # no crash

    @pytest.mark.asyncio
    async def test_send_channel_not_found(self, ch: DiscordChannel) -> None:
        ch._running = True
        ch._client = MagicMock()
        ch._client.is_ready.return_value = True
        ch._client.get_channel.return_value = None

        msg = OutgoingMessage(channel="discord", text="test", metadata={"channel_id": "99"})
        await ch.send(msg)  # no crash

    @pytest.mark.asyncio
    async def test_send_success(self, ch: DiscordChannel) -> None:
        ch._running = True
        ch._client = MagicMock()
        ch._client.is_ready.return_value = True
        mock_channel = MagicMock()
        mock_channel.send = AsyncMock()
        ch._client.get_channel.return_value = mock_channel

        msg = OutgoingMessage(channel="discord", text="hello", metadata={"channel_id": "12345"})
        # Mock circuit breaker to just call the coroutine
        ch._circuit_breaker.call = AsyncMock()
        await ch.send(msg)
        ch._circuit_breaker.call.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_circuit_breaker_open(self, ch: DiscordChannel) -> None:
        from cognithor.utils.circuit_breaker import CircuitBreakerOpen

        ch._running = True
        ch._client = MagicMock()
        ch._client.is_ready.return_value = True
        mock_channel = MagicMock()
        ch._client.get_channel.return_value = mock_channel
        ch._circuit_breaker.call = AsyncMock(side_effect=CircuitBreakerOpen("discord", 60.0))

        msg = OutgoingMessage(channel="discord", text="test", metadata={"channel_id": "12345"})
        await ch.send(msg)  # should not crash

    @pytest.mark.asyncio
    async def test_send_generic_exception(self, ch: DiscordChannel) -> None:
        ch._running = True
        ch._client = MagicMock()
        ch._client.is_ready.return_value = True
        mock_channel = MagicMock()
        ch._client.get_channel.return_value = mock_channel
        ch._circuit_breaker.call = AsyncMock(side_effect=RuntimeError("oops"))

        msg = OutgoingMessage(channel="discord", text="test", metadata={"channel_id": "12345"})
        await ch.send(msg)  # should not crash

    @pytest.mark.asyncio
    async def test_send_rich_not_running(self, ch: DiscordChannel) -> None:
        ch._running = False
        from cognithor.channels.interactive import DiscordMessageBuilder

        builder = MagicMock(spec=DiscordMessageBuilder)
        await ch.send_rich(builder)  # no crash

    @pytest.mark.asyncio
    async def test_send_rich_success(self, ch: DiscordChannel) -> None:
        from cognithor.channels.interactive import DiscordMessageBuilder

        ch._running = True
        ch._client = MagicMock()
        ch._client.is_ready.return_value = True
        mock_channel = MagicMock()
        mock_channel.send = AsyncMock()
        ch._client.get_channel.return_value = mock_channel

        builder = MagicMock(spec=DiscordMessageBuilder)
        builder.build.return_value = {"content": "Rich message content"}
        await ch.send_rich(builder)
        mock_channel.send.assert_called_once_with("Rich message content")

    @pytest.mark.asyncio
    async def test_send_rich_channel_not_found(self, ch: DiscordChannel) -> None:
        from cognithor.channels.interactive import DiscordMessageBuilder

        ch._running = True
        ch._client = MagicMock()
        ch._client.is_ready.return_value = True
        ch._client.get_channel.return_value = None

        builder = MagicMock(spec=DiscordMessageBuilder)
        await ch.send_rich(builder)  # no crash

    @pytest.mark.asyncio
    async def test_send_rich_exception(self, ch: DiscordChannel) -> None:
        from cognithor.channels.interactive import DiscordMessageBuilder

        ch._running = True
        ch._client = MagicMock()
        ch._client.is_ready.return_value = True
        mock_channel = MagicMock()
        mock_channel.send = AsyncMock(side_effect=RuntimeError("fail"))
        ch._client.get_channel.return_value = mock_channel

        builder = MagicMock(spec=DiscordMessageBuilder)
        builder.build.return_value = {"content": "test"}
        await ch.send_rich(builder)  # should not crash

    @pytest.mark.asyncio
    async def test_send_card_not_running(self, ch: DiscordChannel) -> None:
        ch._running = False
        from cognithor.channels.interactive import AdaptiveCard

        card = MagicMock(spec=AdaptiveCard)
        await ch.send_card(card)  # no crash

    @pytest.mark.asyncio
    async def test_send_card_success(self, ch: DiscordChannel) -> None:
        ch._running = True
        ch._client = MagicMock()
        ch._client.is_ready.return_value = True
        mock_channel = MagicMock()
        mock_channel.send = AsyncMock()
        ch._client.get_channel.return_value = mock_channel

        card = MagicMock()
        card.to_discord.return_value = {"content": "Card content"}
        await ch.send_card(card)
        mock_channel.send.assert_called_once_with("Card content")

    @pytest.mark.asyncio
    async def test_send_progress_not_running(self, ch: DiscordChannel) -> None:
        ch._running = False
        from cognithor.channels.interactive import ProgressTracker

        tracker = MagicMock(spec=ProgressTracker)
        await ch.send_progress(tracker)  # no crash

    @pytest.mark.asyncio
    async def test_send_progress_success(self, ch: DiscordChannel) -> None:
        from cognithor.channels.interactive import ProgressTracker

        ch._running = True
        ch._client = MagicMock()
        ch._client.is_ready.return_value = True
        mock_channel = MagicMock()
        mock_channel.send = AsyncMock()
        ch._client.get_channel.return_value = mock_channel

        tracker = MagicMock(spec=ProgressTracker)
        tracker.percent_complete = 75
        await ch.send_progress(tracker)
        mock_channel.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_progress_channel_not_found(self, ch: DiscordChannel) -> None:
        from cognithor.channels.interactive import ProgressTracker

        ch._running = True
        ch._client = MagicMock()
        ch._client.is_ready.return_value = True
        ch._client.get_channel.return_value = None

        tracker = MagicMock(spec=ProgressTracker)
        tracker.percent_complete = 50
        await ch.send_progress(tracker)  # no crash

    @pytest.mark.asyncio
    async def test_send_progress_exception(self, ch: DiscordChannel) -> None:
        from cognithor.channels.interactive import ProgressTracker

        ch._running = True
        ch._client = MagicMock()
        ch._client.is_ready.return_value = True
        mock_channel = MagicMock()
        mock_channel.send = AsyncMock(side_effect=RuntimeError("fail"))
        ch._client.get_channel.return_value = mock_channel

        tracker = MagicMock(spec=ProgressTracker)
        tracker.percent_complete = 50
        await ch.send_progress(tracker)  # should not crash


class TestDiscordApproval:
    @pytest.mark.asyncio
    async def test_approval_not_bidirectional(self, ch: DiscordChannel) -> None:
        ch._bidirectional = False
        action = PlannedAction(tool="test", params={})
        result = await ch.request_approval("s1", action, "reason")
        assert result is False

    @pytest.mark.asyncio
    async def test_approval_channel_not_found(self, ch: DiscordChannel) -> None:
        ch._bidirectional = True
        ch._client = MagicMock()
        ch._client.is_ready.return_value = True
        ch._client.get_channel.return_value = None

        action = PlannedAction(tool="test", params={})
        result = await ch.request_approval("s1", action, "reason")
        assert result is False

    @pytest.mark.asyncio
    async def test_approval_success_flow(self, ch: DiscordChannel) -> None:
        ch._bidirectional = True
        ch._client = MagicMock()
        ch._client.is_ready.return_value = True
        mock_channel = MagicMock()
        mock_msg = MagicMock()
        mock_msg.id = 42
        mock_msg.add_reaction = AsyncMock()
        mock_channel.send = AsyncMock(return_value=mock_msg)
        ch._client.get_channel.return_value = mock_channel

        action = PlannedAction(tool="email", params={"to": "test@test.com"})

        async def approve_after_delay():
            await asyncio.sleep(0.05)
            async with ch._approval_lock:
                entry = ch._approval_messages.get(42)
                if entry:
                    future, _ = entry
                    if not future.done():
                        future.set_result(True)

        task = asyncio.create_task(approve_after_delay())
        result = await ch.request_approval("s1", action, "reason")
        await task
        assert result is True

    @pytest.mark.asyncio
    async def test_approval_timeout(self, ch: DiscordChannel) -> None:
        ch._bidirectional = True
        ch._client = MagicMock()
        ch._client.is_ready.return_value = True
        mock_channel = MagicMock()
        mock_msg = MagicMock()
        mock_msg.id = 43
        mock_msg.add_reaction = AsyncMock()
        mock_channel.send = AsyncMock(return_value=mock_msg)
        ch._client.get_channel.return_value = mock_channel

        action = PlannedAction(tool="test", params={})

        with patch("cognithor.channels.discord.asyncio.wait_for", side_effect=asyncio.TimeoutError):
            result = await ch.request_approval("s1", action, "reason")
        assert result is False

    @pytest.mark.asyncio
    async def test_approval_exception(self, ch: DiscordChannel) -> None:
        ch._bidirectional = True
        ch._client = MagicMock()
        ch._client.is_ready.return_value = True
        ch._client.get_channel.side_effect = RuntimeError("fail")

        action = PlannedAction(tool="test", params={})
        result = await ch.request_approval("s1", action, "reason")
        assert result is False


class TestDiscordOnReactionEdgeCases:
    @pytest.mark.asyncio
    async def test_future_already_done(self, ch: DiscordChannel) -> None:
        ch._client = MagicMock()
        ch._client.user = MagicMock()

        future = asyncio.get_event_loop().create_future()
        future.set_result(True)  # Already resolved
        ch._approval_messages[42] = (future, 123)

        reaction = MagicMock()
        reaction.message.id = 42
        reaction.emoji = "❌"
        user = MagicMock()
        user.id = 123

        await ch._on_reaction(reaction, user)  # should not crash, future already done


class TestDiscordStart:
    @pytest.mark.asyncio
    async def test_start_discord_not_installed(self, ch: DiscordChannel) -> None:
        handler = AsyncMock()
        with patch.dict("sys.modules", {"discord": None}):
            await ch.start(handler)
        assert ch._running is False

    @pytest.mark.asyncio
    async def test_start_with_session_store(self) -> None:
        mock_store = MagicMock()
        mock_store.load_all_channel_mappings.return_value = {"s1": "123"}
        ch = DiscordChannel(token="test", channel_id=12345, session_store=mock_store)

        mock_discord = MagicMock()
        mock_client = MagicMock()
        mock_client.start = AsyncMock()
        mock_discord.Client.return_value = mock_client
        mock_discord.Intents.default.return_value = MagicMock()

        handler = AsyncMock()
        with patch.dict("sys.modules", {"discord": mock_discord}):
            with patch("asyncio.get_running_loop") as mock_loop:
                mock_loop.return_value.create_task = MagicMock()
                await ch.start(handler)

        assert ch._session_users.get("s1") == 123


class TestDiscordStreaming:
    @pytest.mark.asyncio
    async def test_streaming_token(self, ch: DiscordChannel) -> None:
        ch._running = True
        ch._client = MagicMock()
        ch._client.is_ready.return_value = True
        mock_channel = MagicMock()
        mock_channel.send = AsyncMock()
        ch._client.get_channel.return_value = mock_channel

        with patch("cognithor.channels.discord.asyncio.sleep", new_callable=AsyncMock):
            await ch.send_streaming_token("s1", "hello ")


class TestDiscordStop:
    @pytest.mark.asyncio
    async def test_stop(self, ch: DiscordChannel) -> None:
        ch._running = True
        ch._bidirectional = True
        ch._client = MagicMock()
        ch._client.close = AsyncMock()

        await ch.stop()
        assert ch._running is False
        assert ch._bidirectional is False
        assert ch._client is None

    @pytest.mark.asyncio
    async def test_stop_close_error(self, ch: DiscordChannel) -> None:
        ch._running = True
        ch._client = MagicMock()
        ch._client.close = AsyncMock(side_effect=RuntimeError("close failed"))

        await ch.stop()
        assert ch._running is False
        assert ch._client is None
