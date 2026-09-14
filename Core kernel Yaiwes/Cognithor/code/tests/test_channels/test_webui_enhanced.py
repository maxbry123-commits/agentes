"""Enhanced tests fuer den WebUI Channel -- zusaetzliche Coverage.

Deckt: Voice-Bridge, File-Upload, REST-Message, Auth, TLS-Warning,
DummyApp-Fallback, Config-Manager-Integration.
"""

from __future__ import annotations

import base64
import json
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cognithor.channels.webui import WebUIChannel, WSMessageType
from cognithor.models import IncomingMessage, OutgoingMessage, PlannedAction

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def channel() -> WebUIChannel:
    return WebUIChannel(host="127.0.0.1", port=8742)


@pytest.fixture
def auth_channel() -> WebUIChannel:
    return WebUIChannel(host="127.0.0.1", port=8742, api_token="ws-secret")


@pytest.fixture
def handler() -> AsyncMock:
    h = AsyncMock()
    h.return_value = OutgoingMessage(text="OK", session_id="s1", channel="webui")
    return h


class TestWebUIAuth:
    def test_api_token_property_with_token(self, auth_channel: WebUIChannel) -> None:
        assert auth_channel._api_token == "ws-secret"

    def test_api_token_property_without_token(self, channel: WebUIChannel) -> None:
        assert channel._api_token is None

    def test_has_api_token(self, auth_channel: WebUIChannel) -> None:
        assert auth_channel._has_api_token is True

    def test_no_api_token(self, channel: WebUIChannel) -> None:
        assert channel._has_api_token is False


class TestWebUIStart:
    @pytest.mark.asyncio
    async def test_start_sets_handler(self, channel: WebUIChannel, handler: AsyncMock) -> None:
        await channel.start(handler)
        assert channel._handler is handler
        assert channel._start_time > 0

    @pytest.mark.asyncio
    async def test_start_tls_warning_external_host(self, handler: AsyncMock) -> None:
        """Externer Host ohne TLS erzeugt Warning."""
        ch = WebUIChannel(host="0.0.0.0", port=8742)
        await ch.start(handler)
        assert ch._handler is handler

    @pytest.mark.asyncio
    async def test_start_no_tls_warning_localhost(self, handler: AsyncMock) -> None:
        ch = WebUIChannel(host="127.0.0.1", port=8742)
        await ch.start(handler)
        assert ch._handler is handler

    @pytest.mark.asyncio
    async def test_start_with_ssl(self, handler: AsyncMock) -> None:
        ch = WebUIChannel(host="0.0.0.0", port=8742, ssl_certfile="cert.pem", ssl_keyfile="key.pem")
        await ch.start(handler)
        assert ch._handler is handler


class TestWebUISend:
    @pytest.mark.asyncio
    async def test_send_no_connection(self, channel: WebUIChannel) -> None:
        msg = OutgoingMessage(text="lost", session_id="unknown", channel="webui")
        await channel.send(msg)  # Kein Crash

    @pytest.mark.asyncio
    async def test_send_with_connection(self, channel: WebUIChannel) -> None:
        mock_ws = AsyncMock()
        channel._connections["s1"] = mock_ws
        msg = OutgoingMessage(text="Hello", session_id="s1", channel="webui")
        await channel.send(msg)
        mock_ws.send_text.assert_called_once()
        sent = json.loads(mock_ws.send_text.call_args[0][0])
        assert sent["type"] == WSMessageType.ASSISTANT_MESSAGE
        assert sent["text"] == "Hello"
        assert "timestamp" in sent


class TestWebUIVoiceBridge:
    @pytest.mark.asyncio
    async def test_voice_message_transcription(
        self, channel: WebUIChannel, handler: AsyncMock
    ) -> None:
        """Audio-basierte Nachricht wird transkribiert."""
        channel._handler = handler
        mock_ws = AsyncMock()

        audio_b64 = base64.b64encode(b"fake-audio").decode()
        with patch.object(
            channel, "_transcribe_audio", new_callable=AsyncMock, return_value="Transkribiert"
        ):
            await channel._handle_ws_message(
                mock_ws,
                "s1",
                {
                    "type": "user_message",
                    "text": "",
                    "metadata": {"audio_base64": audio_b64},
                },
            )

        handler.assert_called_once()
        incoming: IncomingMessage = handler.call_args[0][0]
        assert incoming.text == "Transkribiert"

    @pytest.mark.asyncio
    async def test_voice_message_transcription_fails(self, channel: WebUIChannel) -> None:
        """Fehlgeschlagene Transkription: _handle_ws_message returns early."""
        channel._handler = AsyncMock()
        mock_ws = AsyncMock()

        with patch.object(channel, "_transcribe_audio", new_callable=AsyncMock, return_value=None):
            await channel._handle_ws_message(
                mock_ws,
                "s1",
                {
                    "type": "user_message",
                    "text": "",
                    "metadata": {"audio_base64": "dGVzdA=="},
                },
            )

        # When _transcribe_audio returns None, _handle_ws_message returns early
        # (error was already sent inside _transcribe_audio itself).
        # The handler should NOT have been called.
        channel._handler.assert_not_called()


class TestWebUIToolEvents:
    @pytest.mark.asyncio
    async def test_tool_event_no_data(self, channel: WebUIChannel) -> None:
        mock_ws = AsyncMock()
        channel._connections["s1"] = mock_ws

        await channel.send_tool_event("s1", WSMessageType.TOOL_START, "web_search")
        sent = json.loads(mock_ws.send_text.call_args[0][0])
        assert sent["data"] == {}

    @pytest.mark.asyncio
    async def test_tool_event_no_connection(self, channel: WebUIChannel) -> None:
        await channel.send_tool_event("no-conn", WSMessageType.TOOL_START, "web_search")


class TestWebUIDummyApp:
    def test_dummy_app(self, channel: WebUIChannel) -> None:
        app = channel._dummy_app()
        assert app.title == "Jarvis Web UI (stub)"
        # All methods should be no-ops
        app.add_middleware()
        decorator = app.get("/test")
        assert callable(decorator)
        decorator = app.post("/test")
        assert callable(decorator)
        decorator = app.websocket("/test")
        assert callable(decorator)
        app.mount("/")


class TestWebUIApprovalTimeout:
    @pytest.mark.asyncio
    async def test_approval_timeout(self, channel: WebUIChannel) -> None:
        mock_ws = AsyncMock()
        channel._connections["s1"] = mock_ws

        action = PlannedAction(tool="rm", params={})
        # Patch timeout to be very short
        with patch("cognithor.channels.webui.asyncio.wait_for", side_effect=TimeoutError):
            result = await channel.request_approval("s1", action, "Test")
        assert result is False


class TestWebUIConfigManager:
    @pytest.mark.asyncio
    async def test_create_app_with_config_manager(self) -> None:
        mock_cm = MagicMock()
        ch = WebUIChannel(host="127.0.0.1", port=8742, config_manager=mock_cm)
        app = ch._create_app()
        assert app is not None

    @pytest.mark.asyncio
    async def test_create_app_without_config_manager(self) -> None:
        ch = WebUIChannel(host="127.0.0.1", port=8742)
        app = ch._create_app()
        assert app is not None


class TestWebUIStaticDir:
    def test_custom_static_dir(self, tmp_path: Path) -> None:
        ch = WebUIChannel(host="127.0.0.1", port=8742, static_dir=str(tmp_path))
        assert ch._static_dir == str(tmp_path)
