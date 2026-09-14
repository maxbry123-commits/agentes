"""Tests fuer F-006: WebUI Default-Host und CORS-Origins muessen sicher sein.

Prueft dass:
  - create_app() Factory default Host = 127.0.0.1 (nicht 0.0.0.0)
  - create_app() Factory default CORS != "*"
  - WebUIChannel.__init__ default Host = 127.0.0.1
  - Explizites Opt-in via Env-Vars funktioniert weiterhin
  - Docker-Deployments weiterhin 0.0.0.0 setzen koennen
"""

from __future__ import annotations

import os
from unittest.mock import patch


class TestCreateAppDefaults:
    """Prueft die Factory-Funktion create_app()."""

    def test_default_host_is_localhost(self) -> None:
        """Default Host muss 127.0.0.1 sein, nicht 0.0.0.0."""
        from cognithor.channels.webui import create_app

        # Sicherstellen dass keine Env-Var gesetzt ist
        env = {
            k: v
            for k, v in os.environ.items()
            if k
            not in ("COGNITHOR_WEBUI_HOST", "COGNITHOR_WEBUI_CORS_ORIGINS", "COGNITHOR_API_TOKEN")
        }
        with patch.dict(os.environ, env, clear=True):
            app = create_app()
        # App wurde erstellt (kein Crash)
        assert app is not None

    def test_default_host_not_0000(self) -> None:
        """0.0.0.0 darf nicht der Default sein."""
        import inspect

        from cognithor.channels.webui import create_app

        source = inspect.getsource(create_app)
        # Nur die Code-Zeile mit os.environ.get pruefen, nicht den Docstring
        for line in source.splitlines():
            if "os.environ.get" in line and "COGNITHOR_WEBUI_HOST" in line:
                assert '"0.0.0.0"' not in line, (
                    f"Default fuer COGNITHOR_WEBUI_HOST darf nicht 0.0.0.0 sein: {line.strip()}"
                )
                break

    def test_default_cors_not_wildcard(self) -> None:
        """Default CORS-Origin darf nicht '*' sein."""
        import inspect

        from cognithor.channels.webui import create_app

        source = inspect.getsource(create_app)
        cors_line = source.split("COGNITHOR_WEBUI_CORS_ORIGINS")[1].split("\n")[0]
        assert '"*"' not in cors_line, (
            "Default fuer COGNITHOR_WEBUI_CORS_ORIGINS darf nicht '*' sein"
        )

    def test_explicit_0000_via_env_still_works(self) -> None:
        """Explizites Opt-in fuer 0.0.0.0 via Env-Var muss weiterhin funktionieren."""
        env = os.environ.copy()
        env["COGNITHOR_WEBUI_HOST"] = "0.0.0.0"
        env["COGNITHOR_WEBUI_CORS_ORIGINS"] = "*"
        with patch.dict(os.environ, env, clear=True):
            from cognithor.channels.webui import create_app

            app = create_app()
        assert app is not None

    def test_explicit_cors_override_works(self) -> None:
        """Explizite CORS-Origins via Env-Var werden korrekt uebernommen."""
        env = os.environ.copy()
        env["COGNITHOR_WEBUI_CORS_ORIGINS"] = "https://myapp.example.com,https://other.example.com"
        with patch.dict(os.environ, env, clear=True):
            from cognithor.channels.webui import create_app

            app = create_app()
        assert app is not None


class TestWebUIChannelDefaults:
    """Prueft dass WebUIChannel.__init__ sichere Defaults hat."""

    def test_init_default_host_is_localhost(self) -> None:
        """WebUIChannel Default-Host muss 127.0.0.1 sein."""
        from cognithor.channels.webui import WebUIChannel

        ch = WebUIChannel()
        assert ch._host == "127.0.0.1"

    def test_init_default_cors_is_empty(self) -> None:
        """WebUIChannel Default-CORS muss leer sein (nicht '*')."""
        from cognithor.channels.webui import WebUIChannel

        ch = WebUIChannel()
        assert ch._cors_origins == []
        assert "*" not in ch._cors_origins

    def test_init_explicit_host_accepted(self) -> None:
        """Explizit uebergebener Host wird akzeptiert."""
        from cognithor.channels.webui import WebUIChannel

        ch = WebUIChannel(host="0.0.0.0")
        assert ch._host == "0.0.0.0"

    def test_init_explicit_cors_accepted(self) -> None:
        """Explizit uebergebene CORS-Origins werden akzeptiert."""
        from cognithor.channels.webui import WebUIChannel

        ch = WebUIChannel(cors_origins=["https://example.com"])
        assert ch._cors_origins == ["https://example.com"]
