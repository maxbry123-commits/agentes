"""Tests fuer den MatrixChannel.

Testet: Lifecycle, Message-Handling, Reaction-Approvals,
Invite-Handling, Senden, Streaming, Hilfsfunktionen.
matrix-nio wird komplett gemockt.
"""

from __future__ import annotations

import asyncio
import sys
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock nio before importing matrix module
_mock_client_instance = MagicMock()
_mock_client_instance.add_event_callback = MagicMock()
_mock_client_instance.login = AsyncMock()
_mock_client_instance.sync = AsyncMock()
_mock_client_instance.close = AsyncMock()
_mock_client_instance.access_token = ""
_mock_client_instance.user_id = ""

_mock_nio = MagicMock()
_mock_nio.AsyncClient = MagicMock(return_value=_mock_client_instance)
_mock_nio.LoginResponse = type("LoginResponse", (), {})
_mock_nio.MatrixRoom = MagicMock
_mock_nio.RoomMessageText = MagicMock()
_mock_nio.UnknownEvent = MagicMock()
_mock_nio.InviteMemberEvent = MagicMock()
sys.modules.setdefault("nio", _mock_nio)

from cognithor.channels.matrix import (
    MAX_MESSAGE_LENGTH,
    MatrixChannel,
    _split_message,
    _text_to_html,
)
from cognithor.models import IncomingMessage, OutgoingMessage, PlannedAction

if TYPE_CHECKING:
    from pathlib import Path


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def matrix_ch(tmp_path: Path) -> MatrixChannel:
    return MatrixChannel(
        homeserver="https://matrix.test",
        user_id="@jarvis:matrix.test",
        access_token="test-token-123",
        allowed_rooms=["!room1:matrix.test"],
        store_path=tmp_path / "matrix_store",
        workspace_dir=tmp_path / "matrix_ws",
    )


@pytest.fixture
def handler() -> AsyncMock:
    h = AsyncMock()
    h.return_value = OutgoingMessage(channel="matrix", text="Antwort", session_id="s1")
    return h


def _make_room(room_id: str = "!room1:matrix.test") -> MagicMock:
    room = MagicMock()
    room.room_id = room_id
    return room


def _make_event(
    sender: str = "@user:matrix.test",
    body: str = "Hallo",
    event_id: str = "$event1",
) -> MagicMock:
    event = MagicMock()
    event.sender = sender
    event.body = body
    event.event_id = event_id
    return event


# ============================================================================
# Properties
# ============================================================================


class TestMatrixProperties:
    def test_name(self, matrix_ch: MatrixChannel) -> None:
        assert matrix_ch.name == "matrix"

    def test_homeserver(self, matrix_ch: MatrixChannel) -> None:
        assert matrix_ch._homeserver == "https://matrix.test"

    def test_access_token_property(self, matrix_ch: MatrixChannel) -> None:
        # Token was stored in token_store
        assert matrix_ch._has_access_token is True

    def test_password_property(self) -> None:
        ch = MatrixChannel(password="test-pwd")
        assert ch._has_password is True


# ============================================================================
# Lifecycle
# ============================================================================


class TestMatrixLifecycle:
    @pytest.mark.asyncio
    async def test_stop_resets_state(self, matrix_ch: MatrixChannel) -> None:
        matrix_ch._running = True
        matrix_ch._client = AsyncMock()

        loop = asyncio.get_running_loop()
        future: asyncio.Future[bool] = loop.create_future()
        matrix_ch._pending_approvals["sess-1"] = future

        await matrix_ch.stop()

        assert matrix_ch._running is False
        assert matrix_ch._client is None
        assert future.done()
        assert future.result() is False

    @pytest.mark.asyncio
    async def test_stop_cancels_sync_task(self, matrix_ch: MatrixChannel) -> None:
        matrix_ch._running = True
        matrix_ch._sync_task = asyncio.create_task(asyncio.sleep(100))
        matrix_ch._client = AsyncMock()

        await matrix_ch.stop()

        assert matrix_ch._sync_task is None

    @pytest.mark.asyncio
    async def test_stop_closes_client(self, matrix_ch: MatrixChannel) -> None:
        mock_client = AsyncMock()
        matrix_ch._client = mock_client
        matrix_ch._running = True

        await matrix_ch.stop()

        mock_client.close.assert_called_once()


# ============================================================================
# Inbound: Message Handling
# ============================================================================


class TestMatrixIncoming:
    @pytest.mark.asyncio
    async def test_on_message_own_ignored(
        self, matrix_ch: MatrixChannel, handler: AsyncMock
    ) -> None:
        """Eigene Nachrichten werden ignoriert."""
        matrix_ch._handler = handler
        room = _make_room()
        event = _make_event(sender="@jarvis:matrix.test")

        await matrix_ch._on_message(room, event)
        handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_message_blocked_room(
        self, matrix_ch: MatrixChannel, handler: AsyncMock
    ) -> None:
        """Nachrichten aus nicht-erlaubten Raeumen werden ignoriert."""
        matrix_ch._handler = handler
        room = _make_room("!other:matrix.test")
        event = _make_event()

        await matrix_ch._on_message(room, event)
        handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_message_empty_text(
        self, matrix_ch: MatrixChannel, handler: AsyncMock
    ) -> None:
        matrix_ch._handler = handler
        room = _make_room()
        event = _make_event(body="")

        await matrix_ch._on_message(room, event)
        handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_message_calls_handler(
        self, matrix_ch: MatrixChannel, handler: AsyncMock
    ) -> None:
        matrix_ch._handler = handler
        with patch.object(matrix_ch, "_send_to_room", new_callable=AsyncMock):
            room = _make_room()
            event = _make_event(body="Hallo Matrix")

            await matrix_ch._on_message(room, event)

        handler.assert_called_once()
        incoming: IncomingMessage = handler.call_args[0][0]
        assert incoming.text == "Hallo Matrix"
        assert incoming.channel == "matrix"
        assert incoming.user_id == "@user:matrix.test"

    @pytest.mark.asyncio
    async def test_on_message_approval_yes(self, matrix_ch: MatrixChannel) -> None:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[bool] = loop.create_future()
        matrix_ch._sessions["!room1:matrix.test"] = "sess-appr"
        matrix_ch._pending_approvals["sess-appr"] = future

        with patch.object(matrix_ch, "_send_to_room", new_callable=AsyncMock):
            room = _make_room()
            event = _make_event(body="ja")
            await matrix_ch._on_message(room, event)

        assert future.done()
        assert future.result() is True

    @pytest.mark.asyncio
    async def test_on_message_approval_no(self, matrix_ch: MatrixChannel) -> None:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[bool] = loop.create_future()
        matrix_ch._sessions["!room1:matrix.test"] = "sess-rej"
        matrix_ch._pending_approvals["sess-rej"] = future

        with patch.object(matrix_ch, "_send_to_room", new_callable=AsyncMock):
            room = _make_room()
            event = _make_event(body="nein")
            await matrix_ch._on_message(room, event)

        assert future.done()
        assert future.result() is False

    @pytest.mark.asyncio
    async def test_on_message_handler_error(self, matrix_ch: MatrixChannel) -> None:
        handler = AsyncMock(side_effect=RuntimeError("Boom"))
        matrix_ch._handler = handler
        with patch.object(matrix_ch, "_send_to_room", new_callable=AsyncMock) as send:
            room = _make_room()
            event = _make_event(body="crash")
            await matrix_ch._on_message(room, event)

            # Fehlermeldung gesendet
            assert send.call_count >= 1

    @pytest.mark.asyncio
    async def test_on_message_no_handler(self, matrix_ch: MatrixChannel) -> None:
        matrix_ch._handler = None
        room = _make_room()
        event = _make_event(body="no handler")
        await matrix_ch._on_message(room, event)  # Kein Crash


# ============================================================================
# Reactions (Approvals)
# ============================================================================


class TestMatrixReactions:
    @pytest.mark.asyncio
    async def test_on_reaction_no_source(self, matrix_ch: MatrixChannel) -> None:
        room = _make_room()
        event = MagicMock(spec=[])  # No source attribute
        await matrix_ch._on_reaction(room, event)  # Kein Crash

    @pytest.mark.asyncio
    async def test_on_reaction_not_annotation(self, matrix_ch: MatrixChannel) -> None:
        room = _make_room()
        event = MagicMock()
        event.source = {"content": {"m.relates_to": {"rel_type": "m.thread"}}}
        await matrix_ch._on_reaction(room, event)  # Kein Crash

    @pytest.mark.asyncio
    async def test_on_reaction_own_ignored(self, matrix_ch: MatrixChannel) -> None:
        room = _make_room()
        event = MagicMock()
        event.source = {
            "sender": "@jarvis:matrix.test",
            "content": {
                "m.relates_to": {
                    "rel_type": "m.annotation",
                    "event_id": "$ev1",
                    "key": "\u2705",
                },
            },
        }
        await matrix_ch._on_reaction(room, event)  # Kein Crash

    @pytest.mark.asyncio
    async def test_on_reaction_approve(self, matrix_ch: MatrixChannel) -> None:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[bool] = loop.create_future()
        matrix_ch._pending_approvals["sess-react"] = future
        matrix_ch._approval_messages["$ev1"] = "sess-react"

        with patch.object(matrix_ch, "_send_to_room", new_callable=AsyncMock):
            room = _make_room()
            event = MagicMock()
            event.source = {
                "sender": "@user:matrix.test",
                "content": {
                    "m.relates_to": {
                        "rel_type": "m.annotation",
                        "event_id": "$ev1",
                        "key": "\u2705",
                    },
                },
            }
            await matrix_ch._on_reaction(room, event)

        assert future.done()
        assert future.result() is True

    @pytest.mark.asyncio
    async def test_on_reaction_reject(self, matrix_ch: MatrixChannel) -> None:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[bool] = loop.create_future()
        matrix_ch._pending_approvals["sess-react2"] = future
        matrix_ch._approval_messages["$ev2"] = "sess-react2"

        with patch.object(matrix_ch, "_send_to_room", new_callable=AsyncMock):
            room = _make_room()
            event = MagicMock()
            event.source = {
                "sender": "@user:matrix.test",
                "content": {
                    "m.relates_to": {
                        "rel_type": "m.annotation",
                        "event_id": "$ev2",
                        "key": "\u274c",
                    },
                },
            }
            await matrix_ch._on_reaction(room, event)

        assert future.done()
        assert future.result() is False

    @pytest.mark.asyncio
    async def test_on_reaction_thumbs_up(self, matrix_ch: MatrixChannel) -> None:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[bool] = loop.create_future()
        matrix_ch._pending_approvals["sess-thumb"] = future
        matrix_ch._approval_messages["$ev3"] = "sess-thumb"

        with patch.object(matrix_ch, "_send_to_room", new_callable=AsyncMock):
            room = _make_room()
            event = MagicMock()
            event.source = {
                "sender": "@user:matrix.test",
                "content": {
                    "m.relates_to": {
                        "rel_type": "m.annotation",
                        "event_id": "$ev3",
                        "key": "\U0001f44d",  # thumbs up
                    },
                },
            }
            await matrix_ch._on_reaction(room, event)

        assert future.done()
        assert future.result() is True

    @pytest.mark.asyncio
    async def test_on_reaction_unknown_event_id(self, matrix_ch: MatrixChannel) -> None:
        room = _make_room()
        event = MagicMock()
        event.source = {
            "sender": "@user:matrix.test",
            "content": {
                "m.relates_to": {
                    "rel_type": "m.annotation",
                    "event_id": "$unknown",
                    "key": "\u2705",
                },
            },
        }
        await matrix_ch._on_reaction(room, event)  # Kein Crash


# ============================================================================
# Invite Handling
# ============================================================================


class TestMatrixInvite:
    @pytest.mark.asyncio
    async def test_on_invite_allowed(self, matrix_ch: MatrixChannel) -> None:
        mock_client = AsyncMock()
        matrix_ch._client = mock_client

        room = _make_room("!room1:matrix.test")
        event = MagicMock()
        await matrix_ch._on_invite(room, event)

        mock_client.join.assert_called_once_with("!room1:matrix.test")

    @pytest.mark.asyncio
    async def test_on_invite_blocked(self, matrix_ch: MatrixChannel) -> None:
        mock_client = AsyncMock()
        matrix_ch._client = mock_client

        room = _make_room("!blocked:matrix.test")
        event = MagicMock()
        await matrix_ch._on_invite(room, event)

        mock_client.join.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_invite_no_client(self, matrix_ch: MatrixChannel) -> None:
        matrix_ch._client = None
        room = _make_room()
        event = MagicMock()
        await matrix_ch._on_invite(room, event)  # Kein Crash

    @pytest.mark.asyncio
    async def test_on_invite_join_error(self, matrix_ch: MatrixChannel) -> None:
        mock_client = AsyncMock()
        mock_client.join = AsyncMock(side_effect=RuntimeError("Join failed"))
        matrix_ch._client = mock_client

        room = _make_room("!room1:matrix.test")
        event = MagicMock()
        await matrix_ch._on_invite(room, event)  # Kein Crash


# ============================================================================
# Send
# ============================================================================


class TestMatrixSend:
    @pytest.mark.asyncio
    async def test_send_not_running(self, matrix_ch: MatrixChannel) -> None:
        matrix_ch._running = False
        msg = OutgoingMessage(channel="matrix", text="noop", session_id="s1")
        await matrix_ch.send(msg)  # Kein Crash

    @pytest.mark.asyncio
    async def test_send_no_room(self, matrix_ch: MatrixChannel) -> None:
        matrix_ch._running = True
        msg = OutgoingMessage(channel="matrix", text="lost", session_id="unknown")
        await matrix_ch.send(msg)  # Kein Crash

    @pytest.mark.asyncio
    async def test_send_via_session(self, matrix_ch: MatrixChannel) -> None:
        matrix_ch._running = True
        matrix_ch._sessions["!room1:matrix.test"] = "sess-x"
        with patch.object(matrix_ch, "_send_to_room", new_callable=AsyncMock) as send:
            msg = OutgoingMessage(channel="matrix", text="Hello", session_id="sess-x")
            await matrix_ch.send(msg)
            send.assert_called_once_with("!room1:matrix.test", "Hello")

    @pytest.mark.asyncio
    async def test_send_via_metadata(self, matrix_ch: MatrixChannel) -> None:
        matrix_ch._running = True
        with patch.object(matrix_ch, "_send_to_room", new_callable=AsyncMock) as send:
            msg = OutgoingMessage(
                channel="matrix",
                text="Hi",
                session_id="unknown",
                metadata={"room_id": "!room1:matrix.test"},
            )
            await matrix_ch.send(msg)
            send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_to_room_no_client(self, matrix_ch: MatrixChannel) -> None:
        matrix_ch._client = None
        result = await matrix_ch._send_to_room("!room1:matrix.test", "noop")
        assert result is None

    @pytest.mark.asyncio
    async def test_send_to_room_success(self, matrix_ch: MatrixChannel) -> None:
        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.event_id = "$sent1"
        mock_client.room_send = AsyncMock(return_value=mock_resp)
        matrix_ch._client = mock_client

        result = await matrix_ch._send_to_room("!room1:matrix.test", "Hallo Raum")
        assert result == "$sent1"

    @pytest.mark.asyncio
    async def test_send_to_room_error(self, matrix_ch: MatrixChannel) -> None:
        mock_client = AsyncMock()
        mock_client.room_send = AsyncMock(side_effect=RuntimeError("Send failed"))
        matrix_ch._client = mock_client

        result = await matrix_ch._send_to_room("!room1:matrix.test", "Error")
        assert result is None


# ============================================================================
# Approval Workflow
# ============================================================================


class TestMatrixApproval:
    @pytest.mark.asyncio
    async def test_approval_no_room(self, matrix_ch: MatrixChannel) -> None:
        action = PlannedAction(tool="delete", params={})
        result = await matrix_ch.request_approval("unknown", action, "Test")
        assert result is False

    @pytest.mark.asyncio
    async def test_approval_timeout(self, matrix_ch: MatrixChannel) -> None:
        matrix_ch._sessions["!room1:matrix.test"] = "sess-t"
        with patch.object(matrix_ch, "_send_to_room", new_callable=AsyncMock, return_value="$ev-t"):
            matrix_ch._client = AsyncMock()
            with patch("cognithor.channels.matrix.APPROVAL_TIMEOUT", 0.05):
                action = PlannedAction(tool="rm", params={})
                result = await matrix_ch.request_approval("sess-t", action, "Danger")
        assert result is False

    @pytest.mark.asyncio
    async def test_resolve_approval(self, matrix_ch: MatrixChannel) -> None:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[bool] = loop.create_future()
        matrix_ch._pending_approvals["sess-ra"] = future
        matrix_ch._sessions["!room1:matrix.test"] = "sess-ra"

        with patch.object(matrix_ch, "_send_to_room", new_callable=AsyncMock):
            await matrix_ch._resolve_approval("sess-ra", approved=True)

        assert future.result() is True


# ============================================================================
# Streaming
# ============================================================================


class TestMatrixStreaming:
    @pytest.mark.asyncio
    async def test_streaming_token(self, matrix_ch: MatrixChannel) -> None:
        matrix_ch._running = True
        matrix_ch._sessions["!room1:matrix.test"] = "sess-s"
        with patch.object(matrix_ch, "send", new_callable=AsyncMock):
            await matrix_ch.send_streaming_token("sess-s", "Token")
            await asyncio.sleep(0.6)


# ============================================================================
# Hilfsfunktionen
# ============================================================================


class TestMatrixHelpers:
    def test_get_or_create_session(self, matrix_ch: MatrixChannel) -> None:
        s1 = matrix_ch._get_or_create_session("!room1:matrix.test")
        s2 = matrix_ch._get_or_create_session("!room1:matrix.test")
        assert s1 == s2

    def test_room_for_session(self, matrix_ch: MatrixChannel) -> None:
        matrix_ch._sessions["!room1:matrix.test"] = "sess-r"
        assert matrix_ch._room_for_session("sess-r") == "!room1:matrix.test"
        assert matrix_ch._room_for_session("unknown") is None

    def test_split_message_short(self) -> None:
        assert _split_message("Hi") == ["Hi"]

    def test_split_message_long(self) -> None:
        long_text = "X" * (MAX_MESSAGE_LENGTH + 100)
        chunks = _split_message(long_text)
        assert len(chunks) >= 2

    def test_text_to_html_bold(self) -> None:
        result = _text_to_html("**bold**")
        assert "<strong>bold</strong>" in result

    def test_text_to_html_italic(self) -> None:
        result = _text_to_html("*italic*")
        assert "<em>italic</em>" in result

    def test_text_to_html_code(self) -> None:
        result = _text_to_html("`code`")
        assert "<code>code</code>" in result

    def test_text_to_html_newlines(self) -> None:
        result = _text_to_html("line1\nline2")
        assert "<br>" in result

    def test_text_to_html_code_block(self) -> None:
        result = _text_to_html("```python\nprint('hi')\n```")
        assert "<pre>" in result
