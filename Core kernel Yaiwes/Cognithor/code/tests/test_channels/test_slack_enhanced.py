"""Enhanced tests for SlackChannel -- additional coverage.

Covers: _on_message, _on_approval, send variants, approval workflow,
streaming tokens, stop, start without app token.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cognithor.channels.slack import SlackChannel
from cognithor.models import OutgoingMessage, PlannedAction


@pytest.fixture
def ch() -> SlackChannel:
    return SlackChannel(token="xoxb-test", app_token="xapp-test", default_channel="C123")


@pytest.fixture
def ch_no_app() -> SlackChannel:
    return SlackChannel(token="xoxb-test")


class TestSlackProperties:
    def test_name(self, ch: SlackChannel) -> None:
        assert ch.name == "slack"

    def test_token(self, ch: SlackChannel) -> None:
        assert ch.token == "xoxb-test"

    def test_app_token(self, ch: SlackChannel) -> None:
        assert ch.app_token == "xapp-test"

    def test_no_app_token(self, ch_no_app: SlackChannel) -> None:
        assert ch_no_app.app_token == ""

    def test_is_bidirectional(self, ch: SlackChannel) -> None:
        assert ch.is_bidirectional is False


class TestSlackOnMessage:
    @pytest.mark.asyncio
    async def test_ignore_own_messages(self, ch: SlackChannel) -> None:
        ch._bot_user_id = "BOT123"
        ch._handler = AsyncMock()
        event = {"user": "BOT123", "text": "hello"}
        await ch._on_message(event)
        ch._handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_ignore_bot_messages(self, ch: SlackChannel) -> None:
        ch._handler = AsyncMock()
        event = {"user": "U999", "bot_id": "B123", "text": "hello"}
        await ch._on_message(event)
        ch._handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_ignore_empty_text(self, ch: SlackChannel) -> None:
        ch._handler = AsyncMock()
        event = {"user": "U123", "text": "   "}
        await ch._on_message(event)
        ch._handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_normal_message(self, ch: SlackChannel) -> None:
        response = OutgoingMessage(channel="slack", text="OK")
        ch._handler = AsyncMock(return_value=response)
        ch._client = AsyncMock()
        ch._bot_user_id = "BOT"

        event = {
            "user": "U123",
            "text": "what is the weather",
            "channel": "C456",
            "ts": "123.456",
        }
        await ch._on_message(event)
        ch._handler.assert_called_once()
        incoming = ch._handler.call_args[0][0]
        assert incoming.text == "what is the weather"
        assert incoming.channel == "slack"

    @pytest.mark.asyncio
    async def test_removes_mention(self, ch: SlackChannel) -> None:
        response = OutgoingMessage(channel="slack", text="OK")
        ch._handler = AsyncMock(return_value=response)
        ch._client = AsyncMock()
        ch._bot_user_id = "BOT123"

        event = {
            "user": "U123",
            "text": "<@BOT123> hello",
            "channel": "C456",
            "ts": "123.456",
        }
        await ch._on_message(event)
        incoming = ch._handler.call_args[0][0]
        assert incoming.text == "hello"


class TestSlackOnApproval:
    @pytest.mark.asyncio
    async def test_approval_approved(self, ch: SlackChannel) -> None:
        future = asyncio.get_event_loop().create_future()
        ch._approval_futures["appr_123"] = future
        ch._client = AsyncMock()

        body = {
            "actions": [{"value": "appr_123"}],
            "user": {"name": "alice"},
            "channel": {"id": "C456"},
            "message": {"ts": "123.456"},
        }
        await ch._on_approval(body, approved=True)
        assert future.result() is True

    @pytest.mark.asyncio
    async def test_approval_denied(self, ch: SlackChannel) -> None:
        future = asyncio.get_event_loop().create_future()
        ch._approval_futures["appr_456"] = future
        ch._client = AsyncMock()

        body = {
            "actions": [{"value": "appr_456"}],
            "user": {"name": "bob"},
            "channel": {"id": "C456"},
            "message": {"ts": "123.456"},
        }
        await ch._on_approval(body, approved=False)
        assert future.result() is False

    @pytest.mark.asyncio
    async def test_approval_unknown_id(self, ch: SlackChannel) -> None:
        ch._client = AsyncMock()
        body = {
            "actions": [{"value": "unknown"}],
            "user": {"name": "alice"},
            "channel": {},
            "message": {},
        }
        await ch._on_approval(body, approved=True)  # no crash


class TestSlackSend:
    @pytest.mark.asyncio
    async def test_send_no_client(self, ch: SlackChannel) -> None:
        ch._client = None
        msg = OutgoingMessage(channel="slack", text="test")
        await ch.send(msg)  # no crash

    @pytest.mark.asyncio
    async def test_send_no_channel(self, ch: SlackChannel) -> None:
        ch._client = AsyncMock()
        ch.default_channel = None
        msg = OutgoingMessage(channel="slack", text="test", metadata={})
        await ch.send(msg)  # no crash

    @pytest.mark.asyncio
    async def test_send_with_thread(self, ch: SlackChannel) -> None:
        ch._client = AsyncMock()
        msg = OutgoingMessage(
            channel="slack",
            text="reply",
            metadata={"channel_id": "C456", "thread_ts": "111.222"},
        )
        await ch.send(msg)
        ch._client.chat_postMessage.assert_called_once()
        kw = ch._client.chat_postMessage.call_args[1]
        assert kw["thread_ts"] == "111.222"

    @pytest.mark.asyncio
    async def test_send_rich_no_client(self, ch: SlackChannel) -> None:
        ch._client = None
        from cognithor.channels.interactive import SlackMessageBuilder

        builder = MagicMock(spec=SlackMessageBuilder)
        await ch.send_rich(builder)  # no crash

    @pytest.mark.asyncio
    async def test_send_card_no_client(self, ch: SlackChannel) -> None:
        ch._client = None
        from cognithor.channels.interactive import AdaptiveCard

        card = MagicMock(spec=AdaptiveCard)
        await ch.send_card(card)  # no crash

    @pytest.mark.asyncio
    async def test_send_progress_no_client(self, ch: SlackChannel) -> None:
        ch._client = None
        from cognithor.channels.interactive import ProgressTracker

        tracker = MagicMock(spec=ProgressTracker)
        await ch.send_progress(tracker)  # no crash


class TestSlackApprovalWorkflow:
    @pytest.mark.asyncio
    async def test_approval_not_bidirectional(self, ch: SlackChannel) -> None:
        ch._bidirectional = False
        action = PlannedAction(tool="test", params={})
        result = await ch.request_approval("s1", action, "reason")
        assert result is False

    @pytest.mark.asyncio
    async def test_approval_no_default_channel(self, ch: SlackChannel) -> None:
        ch._bidirectional = True
        ch._client = AsyncMock()
        ch.default_channel = None
        action = PlannedAction(tool="test", params={})
        result = await ch.request_approval("s1", action, "reason")
        assert result is False

    @pytest.mark.asyncio
    async def test_approval_send_error(self, ch: SlackChannel) -> None:
        ch._bidirectional = True
        ch._client = AsyncMock()
        ch._client.chat_postMessage = AsyncMock(side_effect=RuntimeError("fail"))
        action = PlannedAction(tool="test", params={})
        result = await ch.request_approval("s1", action, "reason")
        assert result is False


class TestSlackStop:
    @pytest.mark.asyncio
    async def test_stop(self, ch: SlackChannel) -> None:
        ch._running = True
        ch._bidirectional = True
        ch._socket_handler = MagicMock()
        ch._socket_handler.close_async = AsyncMock()
        ch._client = AsyncMock()

        await ch.stop()
        assert ch._running is False
        assert ch._bidirectional is False
        assert ch._client is None

    @pytest.mark.asyncio
    async def test_stop_socket_error(self, ch: SlackChannel) -> None:
        ch._running = True
        ch._socket_handler = MagicMock()
        ch._socket_handler.close_async = AsyncMock(side_effect=RuntimeError("err"))
        ch._client = AsyncMock()

        await ch.stop()
        assert ch._running is False


class TestSlackSendRich:
    @pytest.mark.asyncio
    async def test_send_rich_success(self, ch: SlackChannel) -> None:
        from cognithor.channels.interactive import SlackMessageBuilder

        ch._client = AsyncMock()
        builder = MagicMock(spec=SlackMessageBuilder)
        builder.build.return_value = {"text": "Rich msg", "blocks": []}
        await ch.send_rich(builder, channel="C123")
        ch._client.chat_postMessage.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_rich_no_target(self, ch: SlackChannel) -> None:
        from cognithor.channels.interactive import SlackMessageBuilder

        ch._client = AsyncMock()
        ch.default_channel = ""
        builder = MagicMock(spec=SlackMessageBuilder)
        await ch.send_rich(builder)  # no crash, no channel

    @pytest.mark.asyncio
    async def test_send_rich_with_thread(self, ch: SlackChannel) -> None:
        from cognithor.channels.interactive import SlackMessageBuilder

        ch._client = AsyncMock()
        builder = MagicMock(spec=SlackMessageBuilder)
        builder.build.return_value = {"text": "Threaded"}
        await ch.send_rich(builder, channel="C123", thread_ts="111.222")
        kw = ch._client.chat_postMessage.call_args[1]
        assert kw["thread_ts"] == "111.222"

    @pytest.mark.asyncio
    async def test_send_rich_exception(self, ch: SlackChannel) -> None:
        from cognithor.channels.interactive import SlackMessageBuilder

        ch._client = AsyncMock()
        ch._client.chat_postMessage = AsyncMock(side_effect=RuntimeError("fail"))
        builder = MagicMock(spec=SlackMessageBuilder)
        builder.build.return_value = {"text": "test"}
        await ch.send_rich(builder, channel="C123")  # no crash


class TestSlackSendCard:
    @pytest.mark.asyncio
    async def test_send_card_success(self, ch: SlackChannel) -> None:
        from cognithor.channels.interactive import AdaptiveCard

        ch._client = AsyncMock()
        card = MagicMock(spec=AdaptiveCard)
        card.to_slack.return_value = {"text": "Card", "blocks": []}
        await ch.send_card(card, channel="C123")
        ch._client.chat_postMessage.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_card_no_target(self, ch: SlackChannel) -> None:
        from cognithor.channels.interactive import AdaptiveCard

        ch._client = AsyncMock()
        ch.default_channel = ""
        card = MagicMock(spec=AdaptiveCard)
        await ch.send_card(card)  # no crash

    @pytest.mark.asyncio
    async def test_send_card_exception(self, ch: SlackChannel) -> None:
        from cognithor.channels.interactive import AdaptiveCard

        ch._client = AsyncMock()
        ch._client.chat_postMessage = AsyncMock(side_effect=RuntimeError("fail"))
        card = MagicMock(spec=AdaptiveCard)
        card.to_slack.return_value = {"text": "Card"}
        await ch.send_card(card, channel="C123")  # no crash


class TestSlackSendProgress:
    @pytest.mark.asyncio
    async def test_send_progress_success(self, ch: SlackChannel) -> None:
        from cognithor.channels.interactive import ProgressTracker

        ch._client = AsyncMock()
        tracker = MagicMock(spec=ProgressTracker)
        tracker.percent_complete = 75
        tracker.to_slack_blocks.return_value = []
        await ch.send_progress(tracker, channel="C123")
        ch._client.chat_postMessage.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_progress_no_target(self, ch: SlackChannel) -> None:
        from cognithor.channels.interactive import ProgressTracker

        ch._client = AsyncMock()
        ch.default_channel = ""
        tracker = MagicMock(spec=ProgressTracker)
        await ch.send_progress(tracker)  # no crash

    @pytest.mark.asyncio
    async def test_send_progress_exception(self, ch: SlackChannel) -> None:
        from cognithor.channels.interactive import ProgressTracker

        ch._client = AsyncMock()
        ch._client.chat_postMessage = AsyncMock(side_effect=RuntimeError("fail"))
        tracker = MagicMock(spec=ProgressTracker)
        tracker.percent_complete = 50
        tracker.to_slack_blocks.return_value = []
        await ch.send_progress(tracker, channel="C123")  # no crash


class TestSlackSendException:
    @pytest.mark.asyncio
    async def test_send_exception(self, ch: SlackChannel) -> None:
        ch._client = AsyncMock()
        ch._client.chat_postMessage = AsyncMock(side_effect=RuntimeError("fail"))
        msg = OutgoingMessage(channel="slack", text="test", metadata={"channel_id": "C123"})
        await ch.send(msg)  # no crash


class TestSlackStart:
    @pytest.mark.asyncio
    async def test_start_slack_not_installed(self, ch: SlackChannel) -> None:
        handler = AsyncMock()
        with patch.dict("sys.modules", {"slack_sdk": None, "slack_sdk.web.async_client": None}):
            await ch.start(handler)
        assert ch._running is False

    @pytest.mark.asyncio
    async def test_start_no_app_token(self, ch_no_app: SlackChannel) -> None:
        mock_sdk = MagicMock()
        mock_client = AsyncMock()
        mock_client.auth_test = AsyncMock(return_value={"user_id": "BOT", "user": "JarvisBot"})
        mock_sdk.AsyncWebClient.return_value = mock_client

        handler = AsyncMock()
        with (
            patch.dict("sys.modules", {"slack_sdk.web.async_client": mock_sdk}),
            patch("cognithor.channels.slack.AsyncWebClient", mock_sdk.AsyncWebClient, create=True),
        ):
            await ch_no_app.start(handler)

        assert ch_no_app._running is True
        assert ch_no_app._bidirectional is False

    @pytest.mark.asyncio
    async def test_start_auth_test_error(self, ch_no_app: SlackChannel) -> None:
        mock_client = AsyncMock()
        mock_client.auth_test = AsyncMock(side_effect=RuntimeError("auth failed"))

        mock_sdk_module = MagicMock()
        mock_sdk_module.AsyncWebClient = MagicMock(return_value=mock_client)

        handler = AsyncMock()
        with patch.dict(
            "sys.modules",
            {
                "slack_sdk": MagicMock(),
                "slack_sdk.web": MagicMock(),
                "slack_sdk.web.async_client": mock_sdk_module,
            },
        ):
            await ch_no_app.start(handler)

        assert ch_no_app._running is True


class TestSlackApprovalTimeout:
    @pytest.mark.asyncio
    async def test_approval_timeout(self, ch: SlackChannel) -> None:
        ch._bidirectional = True
        ch._client = AsyncMock()
        ch.default_channel = "C123"

        action = PlannedAction(tool="test", params={})
        with patch("cognithor.channels.slack.asyncio.wait_for", side_effect=asyncio.TimeoutError):
            result = await ch.request_approval("s1", action, "reason")
        assert result is False

    @pytest.mark.asyncio
    async def test_approval_success_flow(self, ch: SlackChannel) -> None:
        ch._bidirectional = True
        ch._client = AsyncMock()
        ch.default_channel = "C123"

        action = PlannedAction(tool="email", params={"to": "test@test.com"})

        async def resolve_future():
            await asyncio.sleep(0.05)
            async with ch._approval_lock:
                for _aid, future in ch._approval_futures.items():
                    if not future.done():
                        future.set_result(True)
                        break

        task = asyncio.create_task(resolve_future())
        result = await ch.request_approval("s1", action, "reason")
        await task
        assert result is True


class TestSlackStreaming:
    @pytest.mark.asyncio
    async def test_streaming_token_buffered(self, ch: SlackChannel) -> None:
        ch._client = AsyncMock()
        ch.default_channel = "C123"

        with patch("cognithor.channels.slack.asyncio.sleep", new_callable=AsyncMock):
            await ch.send_streaming_token("s1", "hello ")
