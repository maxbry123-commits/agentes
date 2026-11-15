"""Tests fuer Telegram-Webhook-Modus.

Testet den Webhook-Server, Update-Verarbeitung, Health-Endpoint,
Fallback auf Polling und korrektes Cleanup beim Stoppen.
"""

from __future__ import annotations

import json
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure aiohttp is mockable even when not installed.
# Provide a minimal Response class so `web.Response(status=200).status` works.
if "aiohttp" not in sys.modules:

    class _FakeResponse:
        def __init__(self, *, status: int = 200, text: str = "", body: bytes = b"") -> None:
            self.status = status
            self.text = text
            self.body = body

    def _fake_json_response(data, **kwargs) -> _FakeResponse:
        return _FakeResponse(status=200, body=json.dumps(data).encode())

    _mock_aiohttp_web = MagicMock()
    _mock_aiohttp_web.Response = _FakeResponse
    _mock_aiohttp_web.json_response = _fake_json_response
    _mock_aiohttp = MagicMock()
    _mock_aiohttp.web = _mock_aiohttp_web
    sys.modules["aiohttp"] = _mock_aiohttp
    sys.modules["aiohttp.web"] = _mock_aiohttp_web

from cognithor.channels.telegram import TelegramChannel

# ============================================================================
# Initialization with webhook parameters
# ============================================================================


class TestWebhookInit:
    """Tests fuer die Webhook-Konfiguration bei Initialisierung."""

    def test_default_is_polling(self) -> None:
        """Ohne Webhook-Parameter wird Polling verwendet."""
        ch = TelegramChannel(token="t")
        assert ch._use_webhook is False
        assert ch._webhook_url == ""
        assert ch._webhook_port == 8443
        assert ch._webhook_host == "0.0.0.0"
        assert ch._webhook_runner is None

    def test_webhook_params_stored(self) -> None:
        """Webhook-Parameter werden korrekt gespeichert."""
        ch = TelegramChannel(
            token="t",
            use_webhook=True,
            webhook_url="https://example.com/telegram/webhook",
            webhook_port=9443,
            webhook_host="127.0.0.1",
            ssl_certfile="/path/to/cert.pem",
            ssl_keyfile="/path/to/key.pem",
        )
        assert ch._use_webhook is True
        assert ch._webhook_url == "https://example.com/telegram/webhook"
        assert ch._webhook_port == 9443
        assert ch._webhook_host == "127.0.0.1"
        assert ch._ssl_certfile == "/path/to/cert.pem"
        assert ch._ssl_keyfile == "/path/to/key.pem"


# ============================================================================
# Webhook server start
# ============================================================================


class TestWebhookStart:
    """Tests fuer das Starten des Webhook-Servers."""

    @pytest.mark.asyncio
    async def test_start_webhook_registers_with_telegram(self) -> None:
        """set_webhook wird mit korrekter URL aufgerufen."""
        ch = TelegramChannel(
            token="t",
            use_webhook=True,
            webhook_url="https://bot.example.com/telegram/webhook",
            webhook_port=18443,
            webhook_host="127.0.0.1",
        )

        # Mock python-telegram-bot Application
        mock_app = MagicMock()
        mock_app.initialize = AsyncMock()
        mock_app.start = AsyncMock()
        mock_app.bot.set_webhook = AsyncMock()
        mock_app.add_handler = MagicMock()

        with patch("telegram.ext.Application") as MockAppCls:
            mock_builder = MockAppCls.builder.return_value
            mock_builder.token.return_value.concurrent_updates.return_value.build.return_value = (
                mock_app
            )

            # Patch aiohttp so we don't actually bind a port
            with patch.object(
                TelegramChannel, "_start_webhook", new_callable=AsyncMock
            ) as mock_start_wh:
                await ch.start(handler=AsyncMock())

                mock_start_wh.assert_called_once()
                assert ch._running is True

    @pytest.mark.asyncio
    async def test_start_webhook_calls_set_webhook(self) -> None:
        """_start_webhook registriert den Webhook bei Telegram und startet aiohttp."""
        ch = TelegramChannel(
            token="t",
            use_webhook=True,
            webhook_url="https://bot.example.com/telegram/webhook",
            webhook_port=18443,
            webhook_host="127.0.0.1",
        )

        mock_bot = MagicMock()
        mock_bot.set_webhook = AsyncMock()
        mock_app_obj = MagicMock()
        mock_app_obj.bot = mock_bot
        ch._app = mock_app_obj

        # Patch aiohttp components
        mock_runner = MagicMock()
        mock_runner.setup = AsyncMock()
        mock_site = MagicMock()
        mock_site.start = AsyncMock()

        with (
            patch("aiohttp.web.Application"),
            patch("aiohttp.web.AppRunner", return_value=mock_runner),
            patch("aiohttp.web.TCPSite", return_value=mock_site),
        ):
            await ch._start_webhook()

        mock_bot.set_webhook.assert_called_once()
        call_kwargs = mock_bot.set_webhook.call_args[1]
        assert call_kwargs["url"] == "https://bot.example.com/telegram/webhook"
        assert call_kwargs["drop_pending_updates"] is True
        assert call_kwargs["allowed_updates"] == ["message", "callback_query"]
        # F-024: secret_token wird jetzt mitgeschickt
        assert "secret_token" in call_kwargs
        assert len(call_kwargs["secret_token"]) == 64  # hex(32 bytes)
        assert ch._webhook_runner is mock_runner
        mock_site.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_polling_when_no_webhook_url(self) -> None:
        """Ohne webhook_url wird Polling verwendet (auch wenn use_webhook=True)."""
        ch = TelegramChannel(
            token="t",
            use_webhook=True,
            webhook_url="",  # leer -> Fallback auf Polling
        )

        mock_app = MagicMock()
        mock_app.initialize = AsyncMock()
        mock_app.start = AsyncMock()
        mock_app.updater.start_polling = AsyncMock()
        mock_app.add_handler = MagicMock()

        with patch("telegram.ext.Application") as MockAppCls:
            mock_builder = MockAppCls.builder.return_value
            mock_builder.token.return_value.concurrent_updates.return_value.build.return_value = (
                mock_app
            )

            await ch.start(handler=AsyncMock())

            mock_app.updater.start_polling.assert_called_once_with(drop_pending_updates=True)
            assert ch._running is True

    @pytest.mark.asyncio
    async def test_start_polling_when_use_webhook_false(self) -> None:
        """use_webhook=False nutzt immer Polling."""
        ch = TelegramChannel(
            token="t",
            use_webhook=False,
            webhook_url="https://ignored.example.com/telegram/webhook",
        )

        mock_app = MagicMock()
        mock_app.initialize = AsyncMock()
        mock_app.start = AsyncMock()
        mock_app.updater.start_polling = AsyncMock()
        mock_app.add_handler = MagicMock()

        with patch("telegram.ext.Application") as MockAppCls:
            mock_builder = MockAppCls.builder.return_value
            mock_builder.token.return_value.concurrent_updates.return_value.build.return_value = (
                mock_app
            )

            await ch.start(handler=AsyncMock())

            mock_app.updater.start_polling.assert_called_once_with(drop_pending_updates=True)


# ============================================================================
# Webhook request handling
# ============================================================================


class TestWebhookHandler:
    """Tests fuer die Verarbeitung eingehender Webhook-Requests."""

    @pytest.mark.asyncio
    async def test_valid_update_processed(self) -> None:
        """Gueltiges JSON-Update wird korrekt verarbeitet."""
        ch = TelegramChannel(token="t", use_webhook=True, webhook_url="https://x.com/wh")

        mock_bot = MagicMock()
        mock_app_obj = MagicMock()
        mock_app_obj.bot = mock_bot
        mock_app_obj.process_update = AsyncMock()
        ch._app = mock_app_obj

        update_data = {
            "update_id": 123456,
            "message": {
                "message_id": 1,
                "chat": {"id": 42, "type": "private"},
                "from": {"id": 42, "is_bot": False, "first_name": "Test"},
                "text": "Hello",
                "date": 1700000000,
            },
        }

        mock_request = MagicMock()
        mock_request.json = AsyncMock(return_value=update_data)
        # F-024: Webhook erwartet Secret-Token-Header
        mock_request.headers = MagicMock()
        mock_request.headers.get = lambda key, default="": (
            ch._webhook_secret_token if key == "X-Telegram-Bot-Api-Secret-Token" else default
        )

        mock_update = MagicMock()

        with patch("telegram.Update.de_json", return_value=mock_update) as mock_de_json:
            response = await ch._handle_webhook(mock_request)

        assert response.status == 200
        mock_de_json.assert_called_once_with(update_data, mock_bot)
        mock_app_obj.process_update.assert_called_once_with(mock_update)

    @pytest.mark.asyncio
    async def test_invalid_json_returns_500(self) -> None:
        """Ungueltiges JSON liefert Status 500."""
        ch = TelegramChannel(token="t", use_webhook=True, webhook_url="https://x.com/wh")
        ch._app = MagicMock()

        mock_request = MagicMock()
        mock_request.json = AsyncMock(side_effect=ValueError("bad json"))
        mock_request.headers = MagicMock()
        mock_request.headers.get = lambda key, default="": (
            ch._webhook_secret_token if key == "X-Telegram-Bot-Api-Secret-Token" else default
        )

        response = await ch._handle_webhook(mock_request)
        assert response.status == 500

    @pytest.mark.asyncio
    async def test_process_update_exception_returns_500(self) -> None:
        """Fehler bei process_update liefert Status 500."""
        ch = TelegramChannel(token="t", use_webhook=True, webhook_url="https://x.com/wh")

        mock_app_obj = MagicMock()
        mock_app_obj.bot = MagicMock()
        mock_app_obj.process_update = AsyncMock(side_effect=RuntimeError("processing error"))
        ch._app = mock_app_obj

        update_data = {"update_id": 1}

        mock_request = MagicMock()
        mock_request.json = AsyncMock(return_value=update_data)
        mock_request.headers = MagicMock()
        mock_request.headers.get = lambda key, default="": (
            ch._webhook_secret_token if key == "X-Telegram-Bot-Api-Secret-Token" else default
        )

        with patch("telegram.Update.de_json", return_value=MagicMock()):
            response = await ch._handle_webhook(mock_request)

        assert response.status == 500


# ============================================================================
# Health endpoint
# ============================================================================


class TestWebhookHealth:
    """Tests fuer den Health-Check-Endpoint."""

    @pytest.mark.asyncio
    async def test_health_returns_200(self) -> None:
        """Health-Endpoint liefert Status 200 mit korrekten Feldern."""
        ch = TelegramChannel(token="t", use_webhook=True, webhook_url="https://x.com/wh")
        ch._running = True

        mock_request = MagicMock()
        response = await ch._handle_health(mock_request)

        assert response.status == 200
        body = json.loads(response.body)
        assert body["status"] == "ok"
        assert body["channel"] == "telegram"
        assert body["mode"] == "webhook"
        assert body["running"] is True

    @pytest.mark.asyncio
    async def test_health_not_running(self) -> None:
        """Health-Endpoint zeigt running=False wenn nicht gestartet."""
        ch = TelegramChannel(token="t", use_webhook=True, webhook_url="https://x.com/wh")
        ch._running = False

        mock_request = MagicMock()
        response = await ch._handle_health(mock_request)

        body = json.loads(response.body)
        assert body["running"] is False


# ============================================================================
# Stop / Cleanup
# ============================================================================


class TestWebhookStop:
    """Tests fuer korrektes Cleanup beim Stoppen im Webhook-Modus."""

    @pytest.mark.asyncio
    async def test_stop_calls_delete_webhook(self) -> None:
        """stop() ruft delete_webhook() und runner.cleanup() auf."""
        ch = TelegramChannel(token="t", use_webhook=True, webhook_url="https://x.com/wh")
        ch._running = True

        mock_bot = MagicMock()
        mock_bot.delete_webhook = AsyncMock()

        mock_app = MagicMock()
        mock_app.bot = mock_bot
        mock_app.stop = AsyncMock()
        mock_app.shutdown = AsyncMock()
        ch._app = mock_app

        mock_runner = MagicMock()
        mock_runner.cleanup = AsyncMock()
        ch._webhook_runner = mock_runner

        await ch.stop()

        mock_bot.delete_webhook.assert_called_once_with(drop_pending_updates=False)
        mock_runner.cleanup.assert_called_once()
        mock_app.stop.assert_called_once()
        mock_app.shutdown.assert_called_once()
        assert ch._running is False
        assert ch._app is None
        assert ch._webhook_runner is None

    @pytest.mark.asyncio
    async def test_stop_polling_does_not_call_delete_webhook(self) -> None:
        """Im Polling-Modus wird delete_webhook nicht aufgerufen."""
        ch = TelegramChannel(token="t", use_webhook=False)
        ch._running = True

        mock_app = MagicMock()
        mock_app.bot.delete_webhook = AsyncMock()
        mock_app.updater.stop = AsyncMock()
        mock_app.stop = AsyncMock()
        mock_app.shutdown = AsyncMock()
        ch._app = mock_app

        await ch.stop()

        mock_app.bot.delete_webhook.assert_not_called()
        mock_app.updater.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_webhook_delete_failure_does_not_crash(self) -> None:
        """Fehler bei delete_webhook wird ignoriert (graceful shutdown)."""
        ch = TelegramChannel(token="t", use_webhook=True, webhook_url="https://x.com/wh")
        ch._running = True

        mock_bot = MagicMock()
        mock_bot.delete_webhook = AsyncMock(side_effect=RuntimeError("network error"))

        mock_app = MagicMock()
        mock_app.bot = mock_bot
        mock_app.stop = AsyncMock()
        mock_app.shutdown = AsyncMock()
        ch._app = mock_app

        mock_runner = MagicMock()
        mock_runner.cleanup = AsyncMock()
        ch._webhook_runner = mock_runner

        # Should not raise
        await ch.stop()

        assert ch._running is False
        mock_runner.cleanup.assert_called_once()


# ============================================================================
# Fallback behavior
# ============================================================================


class TestWebhookFallback:
    """Tests fuer Fallback-Verhalten von Webhook auf Polling."""

    def test_empty_webhook_url_means_polling(self) -> None:
        """Leere webhook_url bedeutet effektiv Polling."""
        ch = TelegramChannel(token="t", use_webhook=True, webhook_url="")
        # use_webhook ist True, aber webhook_url ist leer
        # start() prüft: use_webhook AND webhook_url
        assert ch._use_webhook is True
        assert ch._webhook_url == ""

    def test_use_webhook_false_ignores_url(self) -> None:
        """use_webhook=False ignoriert eine gesetzte webhook_url."""
        ch = TelegramChannel(
            token="t",
            use_webhook=False,
            webhook_url="https://set-but-ignored.example.com/wh",
        )
        assert ch._use_webhook is False
