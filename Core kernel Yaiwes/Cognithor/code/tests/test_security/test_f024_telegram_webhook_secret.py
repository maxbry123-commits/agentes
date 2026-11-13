"""Tests fuer F-024: Telegram Webhook ohne secret_token.

Prueft dass:
  - TelegramChannel._webhook_secret_token generiert wird (nicht leer)
  - set_webhook() mit secret_token aufgerufen wird
  - _handle_webhook() den X-Telegram-Bot-Api-Secret-Token Header prueft
  - Fehlender Header → 403
  - Falscher Token → 403
  - Korrekter Token → 200 (Update verarbeitet)
  - hmac.compare_digest verwendet wird (Timing-sicher)
  - Source-Code die Fixes enthaelt
"""

from __future__ import annotations

import inspect
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# telegram-Paket muss importierbar sein — Mock falls nicht installiert
_mock_telegram = MagicMock()
_mock_telegram.Update = MagicMock()
_mock_telegram.ext = MagicMock()
sys.modules.setdefault("telegram", _mock_telegram)
sys.modules.setdefault("telegram.ext", _mock_telegram.ext)
sys.modules.setdefault("telegram.constants", MagicMock())
sys.modules.setdefault("telegram.error", MagicMock())

from cognithor.channels.telegram import TelegramChannel


def _make_channel() -> TelegramChannel:
    """Erstellt einen TelegramChannel mit Webhook-Config."""
    return TelegramChannel(
        token="test-token-123",
        use_webhook=True,
        webhook_url="https://example.com/telegram/webhook",
        webhook_port=8443,
    )


# ============================================================================
# Secret-Token Generation
# ============================================================================


class TestSecretTokenGeneration:
    """Prueft dass ein Secret-Token generiert wird."""

    def test_secret_token_not_empty(self) -> None:
        ch = _make_channel()
        assert ch._webhook_secret_token != ""

    def test_secret_token_sufficient_length(self) -> None:
        """Token muss mindestens 32 Hex-Zeichen haben (16 Bytes)."""
        ch = _make_channel()
        assert len(ch._webhook_secret_token) >= 32

    def test_secret_token_is_hex(self) -> None:
        ch = _make_channel()
        int(ch._webhook_secret_token, 16)  # Wirft ValueError wenn nicht hex

    def test_secret_token_unique_per_instance(self) -> None:
        ch1 = _make_channel()
        ch2 = _make_channel()
        assert ch1._webhook_secret_token != ch2._webhook_secret_token


# ============================================================================
# Webhook Handler Verification
# ============================================================================


class TestWebhookHandlerVerification:
    """Prueft die Secret-Token-Verifizierung im Handler."""

    def _make_request(self, secret_token: str | None = None) -> MagicMock:
        """Erstellt ein Mock-Request mit optionalem Secret-Token Header."""
        request = MagicMock()
        headers = MagicMock()
        if secret_token is not None:
            headers.get = MagicMock(
                side_effect=lambda key, default="": (
                    secret_token if key == "X-Telegram-Bot-Api-Secret-Token" else default
                ),
            )
        else:
            headers.get = MagicMock(return_value="")
        request.headers = headers
        return request

    @pytest.mark.asyncio
    async def test_missing_header_returns_403(self) -> None:
        ch = _make_channel()
        ch._app = MagicMock()

        request = self._make_request(secret_token=None)
        response = await ch._handle_webhook(request)
        assert response.status == 403

    @pytest.mark.asyncio
    async def test_wrong_token_returns_403(self) -> None:
        ch = _make_channel()
        ch._app = MagicMock()

        request = self._make_request(secret_token="wrong-token")
        response = await ch._handle_webhook(request)
        assert response.status == 403

    @pytest.mark.asyncio
    async def test_correct_token_returns_200(self) -> None:
        ch = _make_channel()
        ch._app = MagicMock()

        mock_update = MagicMock()
        with patch("telegram.Update.de_json", return_value=mock_update):
            ch._app.process_update = AsyncMock()

            request = self._make_request(secret_token=ch._webhook_secret_token)
            request.json = AsyncMock(return_value={"update_id": 1})

            response = await ch._handle_webhook(request)
            assert response.status == 200

    @pytest.mark.asyncio
    async def test_empty_token_header_returns_403(self) -> None:
        ch = _make_channel()
        ch._app = MagicMock()

        request = self._make_request(secret_token="")
        response = await ch._handle_webhook(request)
        assert response.status == 403


# ============================================================================
# set_webhook Integration
# ============================================================================


class TestSetWebhookSecretToken:
    """Prueft dass set_webhook() den secret_token uebergibt."""

    def test_source_passes_secret_token(self) -> None:
        """set_webhook() Aufruf enthaelt secret_token Parameter."""
        source = inspect.getsource(TelegramChannel._start_webhook)
        assert "secret_token=" in source
        assert "_webhook_secret_token" in source


# ============================================================================
# Source-Level-Checks
# ============================================================================


class TestSourceLevelChecks:
    """Prueft den Source-Code auf die Fixes."""

    def test_init_generates_secret(self) -> None:
        source = inspect.getsource(TelegramChannel.__init__)
        assert "_webhook_secret_token" in source
        assert "token_hex" in source

    def test_handler_checks_header(self) -> None:
        source = inspect.getsource(TelegramChannel._handle_webhook)
        assert "X-Telegram-Bot-Api-Secret-Token" in source

    def test_handler_uses_compare_digest(self) -> None:
        source = inspect.getsource(TelegramChannel._handle_webhook)
        assert "compare_digest" in source

    def test_handler_returns_403_on_mismatch(self) -> None:
        source = inspect.getsource(TelegramChannel._handle_webhook)
        assert "403" in source

    def test_handler_logs_warning(self) -> None:
        source = inspect.getsource(TelegramChannel._handle_webhook)
        assert "warning" in source.lower() or "Warning" in source
