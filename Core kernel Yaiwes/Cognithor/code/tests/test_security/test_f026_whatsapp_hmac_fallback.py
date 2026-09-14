"""Tests fuer F-026: WhatsApp HMAC Fallback auf API-Token.

Prueft dass:
  - Ohne app_secret gibt _verify_signature() False zurueck (nicht API-Token-Fallback)
  - Mit app_secret wird korrekt verifiziert
  - Falsche Signatur wird abgelehnt
  - Korrekte Signatur wird akzeptiert
  - Leerer signature_header wird abgelehnt
  - Falsches Praefix (nicht sha256=) wird abgelehnt
  - _setup_webhook loggt Warning wenn app_secret fehlt
  - Source-Code keinen API-Token-Fallback mehr hat
"""

from __future__ import annotations

import hashlib
import hmac as hmac_mod
import inspect
import sys
from unittest.mock import MagicMock

# faster_whisper kann fehlen
sys.modules.setdefault("faster_whisper", MagicMock())

from cognithor.channels.whatsapp import WhatsAppChannel


def _make_channel(app_secret: str = "") -> WhatsAppChannel:
    """Erstellt einen WhatsAppChannel mit optionalem app_secret."""
    return WhatsAppChannel(
        api_token="test-api-token-123",
        phone_number_id="12345",
        app_secret=app_secret,
    )


# ============================================================================
# Ohne app_secret
# ============================================================================


class TestWithoutAppSecret:
    """Prueft Verhalten ohne konfiguriertes app_secret."""

    def test_verify_returns_false_without_secret(self) -> None:
        """Ohne app_secret: _verify_signature gibt False zurueck."""
        ch = _make_channel(app_secret="")
        payload = b'{"test": true}'
        # Erstelle gueltige Signatur mit API-Token (alter Fallback-Bug)
        sig = hmac_mod.new(
            b"test-api-token-123",
            payload,
            hashlib.sha256,
        ).hexdigest()

        result = ch._verify_signature(payload, f"sha256={sig}")
        assert result is False

    def test_verify_false_even_with_valid_looking_sig(self) -> None:
        """Auch mit korrektem Format: ohne app_secret immer False."""
        ch = _make_channel(app_secret="")
        result = ch._verify_signature(b"data", "sha256=abc123")
        assert result is False

    def test_no_api_token_fallback(self) -> None:
        """Source-Code darf nicht _api_token als Fallback verwenden."""
        source = inspect.getsource(WhatsAppChannel._verify_signature)
        assert "_api_token" not in source


# ============================================================================
# Mit app_secret
# ============================================================================


class TestWithAppSecret:
    """Prueft korrekte HMAC-Verifizierung mit app_secret."""

    def test_correct_signature_accepted(self) -> None:
        ch = _make_channel(app_secret="my-secret-key")
        payload = b'{"entry": []}'
        sig = hmac_mod.new(
            b"my-secret-key",
            payload,
            hashlib.sha256,
        ).hexdigest()

        result = ch._verify_signature(payload, f"sha256={sig}")
        assert result is True

    def test_wrong_signature_rejected(self) -> None:
        ch = _make_channel(app_secret="my-secret-key")
        payload = b'{"entry": []}'

        result = ch._verify_signature(payload, "sha256=wronghash")
        assert result is False

    def test_tampered_payload_rejected(self) -> None:
        """Signatur fuer originalen Payload, aber anderer Payload gesendet."""
        ch = _make_channel(app_secret="my-secret-key")
        original = b'{"entry": []}'
        sig = hmac_mod.new(
            b"my-secret-key",
            original,
            hashlib.sha256,
        ).hexdigest()

        tampered = b'{"entry": [{"evil": true}]}'
        result = ch._verify_signature(tampered, f"sha256={sig}")
        assert result is False

    def test_empty_signature_header_rejected(self) -> None:
        ch = _make_channel(app_secret="my-secret-key")
        result = ch._verify_signature(b"data", "")
        assert result is False

    def test_missing_sha256_prefix_rejected(self) -> None:
        ch = _make_channel(app_secret="my-secret-key")
        result = ch._verify_signature(b"data", "md5=abc123")
        assert result is False

    def test_different_secrets_different_sigs(self) -> None:
        """Unterschiedliche Secrets erzeugen unterschiedliche Signaturen."""
        payload = b"same payload"

        ch1 = _make_channel(app_secret="secret-1")
        sig1 = hmac_mod.new(b"secret-1", payload, hashlib.sha256).hexdigest()
        assert ch1._verify_signature(payload, f"sha256={sig1}") is True

        ch2 = _make_channel(app_secret="secret-2")
        assert ch2._verify_signature(payload, f"sha256={sig1}") is False


# ============================================================================
# Startup Warning
# ============================================================================


class TestStartupWarning:
    """Prueft dass _setup_webhook bei fehlendem app_secret warnt."""

    def test_setup_webhook_warns_without_secret(self) -> None:
        source = inspect.getsource(WhatsAppChannel._setup_webhook)
        assert "app_secret" in source
        assert "nicht konfiguriert" in source or "not configured" in source


# ============================================================================
# Source-Level-Checks
# ============================================================================


class TestSourceLevelChecks:
    """Prueft den Source-Code auf den Fix."""

    def test_no_api_token_in_verify(self) -> None:
        """_verify_signature darf _api_token nicht verwenden."""
        source = inspect.getsource(WhatsAppChannel._verify_signature)
        assert "_api_token" not in source

    def test_checks_app_secret_first(self) -> None:
        """Erste Pruefung: ist app_secret vorhanden?"""
        source = inspect.getsource(WhatsAppChannel._verify_signature)
        assert "not self._app_secret" in source

    def test_uses_app_secret_for_hmac(self) -> None:
        """HMAC wird mit _app_secret berechnet."""
        source = inspect.getsource(WhatsAppChannel._verify_signature)
        assert "self._app_secret.encode" in source

    def test_logs_error_without_secret(self) -> None:
        source = inspect.getsource(WhatsAppChannel._verify_signature)
        assert "logger.error" in source

    def test_uses_compare_digest(self) -> None:
        source = inspect.getsource(WhatsAppChannel._verify_signature)
        assert "compare_digest" in source
