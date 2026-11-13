"""Tests fuer F-015: Matrix stille Fallback auf unverschluesselt.

Prueft dass:
  - Warnung geloggt wird wenn olm nicht verfuegbar ist
  - require_e2ee Parameter existiert (Default False)
  - Bei require_e2ee=True und fehlendem olm: Start wird verweigert
  - Bei require_e2ee=False und fehlendem olm: Warnung, aber Start erlaubt
  - Bei vorhandenem olm: keine Warnung
  - Source-Code die E2EE-Pruefung enthaelt
"""

from __future__ import annotations

import inspect
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock nio before importing MatrixChannel (nio ist nicht installiert)
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

# Mock faster_whisper to avoid torch import crash
sys.modules.setdefault("faster_whisper", MagicMock())

from typing import TYPE_CHECKING

from cognithor.channels.matrix import MatrixChannel

if TYPE_CHECKING:
    from pathlib import Path


def _make_ch(tmp_path: Path, **kwargs) -> MatrixChannel:
    """Erstellt einen MatrixChannel mit Test-Defaults."""
    defaults = dict(
        homeserver="https://matrix.test",
        user_id="@bot:test",
        access_token="tok123",
        store_path=tmp_path / "store",
        workspace_dir=tmp_path / "ws",
    )
    defaults.update(kwargs)
    return MatrixChannel(**defaults)


class TestRequireE2EEParameter:
    """Prueft dass der require_e2ee Parameter existiert."""

    def test_constructor_accepts_require_e2ee(self) -> None:
        ch = MatrixChannel(require_e2ee=True)
        assert ch._require_e2ee is True

    def test_default_require_e2ee_is_false(self) -> None:
        ch = MatrixChannel()
        assert ch._require_e2ee is False

    def test_constructor_signature_has_require_e2ee(self) -> None:
        sig = inspect.signature(MatrixChannel.__init__)
        assert "require_e2ee" in sig.parameters
        assert sig.parameters["require_e2ee"].default is False


class TestOlmNotAvailable:
    """Prueft Verhalten wenn olm nicht installiert ist."""

    @pytest.mark.asyncio
    async def test_warning_when_olm_missing(self, tmp_path: Path) -> None:
        """Warnung muss geloggt werden wenn olm fehlt."""
        ch = _make_ch(tmp_path)

        with patch("cognithor.channels.matrix.logger") as mock_logger:
            with patch.dict("sys.modules", {"olm": None}):
                with patch.object(ch, "_sync_loop", new_callable=AsyncMock):
                    await ch.start(AsyncMock())

            warning_calls = [str(c) for c in mock_logger.warning.call_args_list]
            assert any("UNVERSCHLUESSELT" in w for w in warning_calls), (
                f"Keine Warnung ueber unverschluesselte Nachrichten. Warning-Calls: {warning_calls}"
            )

        await ch.stop()

    @pytest.mark.asyncio
    async def test_require_e2ee_blocks_start(self, tmp_path: Path) -> None:
        """Bei require_e2ee=True und fehlendem olm: Start abgebrochen."""
        ch = _make_ch(tmp_path, require_e2ee=True)

        with patch("cognithor.channels.matrix.logger") as mock_logger:
            with patch.dict("sys.modules", {"olm": None}):
                with patch.object(ch, "_sync_loop", new_callable=AsyncMock):
                    await ch.start(AsyncMock())

            error_calls = [str(c) for c in mock_logger.error.call_args_list]
            assert any("require_e2ee" in e for e in error_calls)

        # Client darf nicht gesetzt sein
        assert ch._client is None
        assert ch._running is False

    @pytest.mark.asyncio
    async def test_no_require_e2ee_allows_start(self, tmp_path: Path) -> None:
        """Bei require_e2ee=False und fehlendem olm: Start erlaubt."""
        ch = _make_ch(tmp_path, require_e2ee=False)

        with patch.dict("sys.modules", {"olm": None}):
            with patch.object(ch, "_sync_loop", new_callable=AsyncMock):
                await ch.start(AsyncMock())

        assert ch._client is not None
        assert ch._running is True
        await ch.stop()


class TestOlmAvailable:
    """Prueft Verhalten wenn olm installiert ist."""

    @pytest.mark.asyncio
    async def test_no_warning_when_olm_present(self, tmp_path: Path) -> None:
        """Keine Warnung wenn olm verfuegbar ist."""
        ch = _make_ch(tmp_path)

        fake_olm = MagicMock()
        with patch("cognithor.channels.matrix.logger") as mock_logger:
            with patch.dict("sys.modules", {"olm": fake_olm}):
                with patch.object(ch, "_sync_loop", new_callable=AsyncMock):
                    await ch.start(AsyncMock())

            warning_calls = [str(c) for c in mock_logger.warning.call_args_list]
            assert not any("UNVERSCHLUESSELT" in w for w in warning_calls)

        await ch.stop()


class TestSourceLevelChecks:
    """Prueft den Source-Code auf E2EE-Pruefung."""

    def test_start_checks_olm(self) -> None:
        source = inspect.getsource(MatrixChannel.start)
        assert "olm" in source

    def test_start_logs_warning_for_missing_olm(self) -> None:
        source = inspect.getsource(MatrixChannel.start)
        assert "UNVERSCHLUESSELT" in source

    def test_start_checks_require_e2ee(self) -> None:
        source = inspect.getsource(MatrixChannel.start)
        assert "require_e2ee" in source

    def test_start_returns_early_when_required(self) -> None:
        source = inspect.getsource(MatrixChannel.start)
        # Muss ein return vor dem AsyncClient() Aufruf geben
        require_idx = source.index("require_e2ee")
        return_after = source.index("return", require_idx)
        client_create = source.index("AsyncClient(")
        assert return_after < client_create
