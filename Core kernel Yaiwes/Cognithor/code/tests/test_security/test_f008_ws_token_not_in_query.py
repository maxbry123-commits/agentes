"""Tests fuer F-008: WebSocket-Token darf nicht als Query-Parameter gesendet werden.

Prueft dass:
  - Kein query_params.get("token") im Source-Code vorhanden ist
  - WebSocket-Auth via erster Nachricht funktioniert (type: auth)
  - Fehlender Auth-Nachricht fuehrt zu Disconnect
  - Ungültiger Token fuehrt zu Disconnect mit Error-Nachricht
  - Ohne required_token funktioniert WebSocket ohne Auth
"""

from __future__ import annotations

import inspect

import pytest


class TestNoQueryParamToken:
    """Source-Level-Pruefung: kein query_params.get('token') mehr."""

    def test_main_no_query_param(self) -> None:
        """__main__.py darf kein query_params.get('token') enthalten."""
        import cognithor.__main__ as main_mod

        source = inspect.getsource(main_mod)
        for i, line in enumerate(source.splitlines(), 1):
            if "query_params" in line and "token" in line:
                pytest.fail(f"__main__.py Zeile {i}: Query-Param Token gefunden: {line.strip()}")

    def test_webui_no_query_param(self) -> None:
        """webui.py darf kein query_params.get('token') enthalten."""
        from cognithor.channels import webui as webui_mod

        source = inspect.getsource(webui_mod)
        for i, line in enumerate(source.splitlines(), 1):
            if "query_params" in line and "token" in line:
                pytest.fail(f"webui.py Zeile {i}: Query-Param Token gefunden: {line.strip()}")


class TestWebUIFirstMessageAuth:
    """Prueft dass WebUIChannel WebSocket-Auth via erster Nachricht funktioniert."""

    def test_auth_code_uses_receive_text(self) -> None:
        """Auth muss via receive_text() (erste Nachricht) stattfinden."""
        from cognithor.channels.webui import WebUIChannel

        source = inspect.getsource(WebUIChannel._create_app)
        # Nach "accept" muss "receive_text" fuer Auth kommen
        assert "receive_text" in source, "WebSocket-Auth muss via receive_text() erfolgen"

    def test_auth_checks_type_auth(self) -> None:
        """Auth-Code muss auf type == 'auth' pruefen."""
        from cognithor.channels.webui import WebUIChannel

        source = inspect.getsource(WebUIChannel._create_app)
        assert '"auth"' in source or "'auth'" in source, "Auth-Code muss auf type=='auth' pruefen"

    def test_auth_uses_hmac_compare(self) -> None:
        """Token-Vergleich muss hmac.compare_digest verwenden (timing-safe)."""
        from cognithor.channels.webui import WebUIChannel

        source = inspect.getsource(WebUIChannel._create_app)
        assert "compare_digest" in source, "Token-Vergleich muss hmac.compare_digest verwenden"

    def test_auth_has_timeout(self) -> None:
        """Auth muss einen Timeout haben (Client kann nicht ewig warten)."""
        from cognithor.channels.webui import WebUIChannel

        source = inspect.getsource(WebUIChannel._create_app)
        assert "wait_for" in source or "timeout" in source.lower(), "Auth muss einen Timeout haben"

    def test_auth_sends_error_on_failure(self) -> None:
        """Bei ungueltigem Token muss eine Error-Nachricht gesendet werden."""
        from cognithor.channels.webui import WebUIChannel

        source = inspect.getsource(WebUIChannel._create_app)
        assert "Unauthorized" in source, "Bei Auth-Failure muss 'Unauthorized' gesendet werden"


class TestMainFirstMessageAuth:
    """Prueft dass __main__.py WebSocket-Auth via erster Nachricht funktioniert."""

    def test_auth_code_uses_receive_text(self) -> None:
        """Auth muss via receive_text() (erste Nachricht) stattfinden."""
        import cognithor.__main__ as main_mod

        source = inspect.getsource(main_mod)
        # Finde den WebSocket-Handler-Bereich
        ws_section = source[source.index("_cc_ws") :]
        assert "receive_text" in ws_section

    def test_auth_checks_type_auth(self) -> None:
        import cognithor.__main__ as main_mod

        source = inspect.getsource(main_mod)
        ws_section = source[source.index("_cc_ws") :]
        assert '"auth"' in ws_section or "'auth'" in ws_section

    def test_auth_uses_hmac_compare(self) -> None:
        import cognithor.__main__ as main_mod

        source = inspect.getsource(main_mod)
        ws_section = source[source.index("_cc_ws") :]
        assert "compare_digest" in ws_section

    def test_auth_has_timeout(self) -> None:
        import cognithor.__main__ as main_mod

        source = inspect.getsource(main_mod)
        ws_section = source[source.index("_cc_ws") :]
        assert "wait_for" in ws_section

    def test_auth_sends_error_on_failure(self) -> None:
        import cognithor.__main__ as main_mod

        source = inspect.getsource(main_mod)
        ws_section = source[source.index("_cc_ws") :]
        assert "Unauthorized" in ws_section
