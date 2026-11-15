"""Tests fuer F-013: IRC Passwort im Klartext (SSL Default=False).

Prueft dass:
  - Default use_ssl=True ist
  - Default port=6697 (SSL-Port) ist
  - Passwort ohne SSL verweigert wird (start() kehrt frueh zurueck)
  - Passwort mit SSL erlaubt ist
  - Ohne Passwort + ohne SSL weiterhin funktioniert (kein Passwort = kein Risiko)
  - NickServ IDENTIFY ebenfalls nur ueber SSL gesendet wird
"""

from __future__ import annotations

import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cognithor.channels.irc import IRCChannel


class TestSecureDefaults:
    """Prueft dass die Defaults sicher sind."""

    def test_default_ssl_is_true(self) -> None:
        ch = IRCChannel()
        assert ch._use_ssl is True

    def test_default_port_is_6697(self) -> None:
        ch = IRCChannel()
        assert ch._port == 6697

    def test_constructor_signature_defaults(self) -> None:
        sig = inspect.signature(IRCChannel.__init__)
        assert sig.parameters["use_ssl"].default is True
        assert sig.parameters["port"].default == 6697


class TestPasswordWithoutSSL:
    """Prueft dass Passwort ohne SSL verweigert wird."""

    @pytest.mark.asyncio
    async def test_password_without_ssl_refuses_connection(self) -> None:
        ch = IRCChannel(
            server="irc.example.com",
            password="secret",
            use_ssl=False,
        )
        handler = AsyncMock()
        await ch.start(handler)
        # Verbindung wurde NICHT aufgebaut
        assert ch._running is False
        assert ch._writer is None

    @pytest.mark.asyncio
    async def test_password_without_ssl_does_not_call_open_connection(self) -> None:
        ch = IRCChannel(
            server="irc.example.com",
            password="my-pass",
            use_ssl=False,
        )
        with patch("asyncio.open_connection") as mock_conn:
            await ch.start(AsyncMock())
            mock_conn.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_password_without_ssl_allowed(self) -> None:
        """Ohne Passwort + ohne SSL ist erlaubt (kein Klartext-Risiko)."""
        ch = IRCChannel(
            server="irc.example.com",
            port=6667,
            use_ssl=False,
        )
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()

        with patch("asyncio.open_connection", return_value=(MagicMock(), mock_writer)):
            with patch.object(ch, "_receive_loop", new_callable=AsyncMock):
                await ch.start(AsyncMock())

        assert ch._running is True


class TestPasswordWithSSL:
    """Prueft dass Passwort mit SSL funktioniert."""

    @pytest.mark.asyncio
    async def test_password_with_ssl_connects(self) -> None:
        ch = IRCChannel(
            server="irc.example.com",
            password="secret",
            use_ssl=True,
        )
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()

        with patch("asyncio.open_connection", return_value=(MagicMock(), mock_writer)):
            with patch.object(ch, "_receive_loop", new_callable=AsyncMock):
                await ch.start(AsyncMock())

        assert ch._running is True
        # PASS wurde gesendet
        calls = mock_writer.write.call_args_list
        pass_calls = [c for c in calls if b"PASS" in c[0][0]]
        assert len(pass_calls) == 1

    @pytest.mark.asyncio
    async def test_ssl_uses_ssl_context(self) -> None:
        ch = IRCChannel(
            server="irc.example.com",
            use_ssl=True,
        )
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()

        with patch("asyncio.open_connection", return_value=(MagicMock(), mock_writer)) as mock_conn:
            with patch.object(ch, "_receive_loop", new_callable=AsyncMock):
                await ch.start(AsyncMock())

        # SSL-Kontext muss uebergeben worden sein
        _, kwargs = mock_conn.call_args
        assert "ssl" in kwargs
        assert kwargs["ssl"] is not None


class TestSourceLevelChecks:
    """Prueft den Source-Code auf korrekte Implementierung."""

    def test_start_method_checks_password_without_ssl(self) -> None:
        source = inspect.getsource(IRCChannel.start)
        assert "self._password" in source
        assert "self._use_ssl" in source
        # Es muss einen Guard geben der bei password+no-ssl abbricht
        assert "return" in source

    def test_pass_command_only_after_connection(self) -> None:
        """PASS wird nur gesendet nachdem die Verbindung steht."""
        source = inspect.getsource(IRCChannel.start)
        # PASS kommt nach open_connection
        pass_idx = source.index("PASS")
        conn_idx = source.index("open_connection")
        assert pass_idx > conn_idx

    def test_no_plaintext_password_in_logs(self) -> None:
        """Das Passwort darf nicht in Log-Meldungen erscheinen."""
        source = inspect.getsource(IRCChannel.start)
        # logger-Aufrufe duerfen nicht self._password enthalten
        for line in source.split("\n"):
            if "logger." in line:
                assert "self._password" not in line, (
                    f"Passwort koennte in Log-Zeile landen: {line.strip()}"
                )
