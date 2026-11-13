"""Tests fuer F-003: MCP auth_token darf nicht im Klartext via GET exponiert werden.

Prueft dass:
  - auth_token in der GET /api/v1/mcp-servers Response maskiert wird
  - Leeres auth_token bleibt leer (nicht maskiert)
  - PUT weiterhin auth_token im Klartext akzeptiert und speichert
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml


def _setup_app_with_mcp_file(mcp_data: dict) -> tuple:
    """Erstellt FakeApp mit registrierten Routes und einer temp MCP-YAML-Datei."""
    from tests.test_channels.test_config_routes import FakeApp

    tmpfile = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".yaml",
        delete=False,
        encoding="utf-8",
    )
    yaml.dump(mcp_data, tmpfile, default_flow_style=False)
    tmpfile.close()

    app = FakeApp()
    config_manager = MagicMock()
    config_manager.config.mcp_config_file = Path(tmpfile.name)
    gateway = MagicMock()

    from cognithor.channels.config_routes import create_config_routes

    create_config_routes(app, config_manager, gateway=gateway)
    return app, Path(tmpfile.name)


@pytest.mark.asyncio
async def test_auth_token_masked_in_get_response() -> None:
    """GET /api/v1/mcp-servers muss auth_token als '***' maskieren."""
    app, tmp = _setup_app_with_mcp_file(
        {
            "server_mode": {
                "mode": "enabled",
                "auth_token": "sk-super-secret-token-12345",
                "require_auth": True,
            },
            "servers": {},
        }
    )
    try:
        handler = app.routes["GET /api/v1/mcp-servers"]
        result = await handler()
        assert result["auth_token"] == "***", (
            f"auth_token sollte maskiert sein, war aber: {result['auth_token']}"
        )
        assert "sk-super-secret-token-12345" not in str(result), (
            "Klartext-Token darf nicht in der Response auftauchen"
        )
        assert result["mode"] == "enabled"
        assert result["require_auth"] is True
    finally:
        tmp.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_empty_auth_token_stays_empty() -> None:
    """Leeres auth_token wird nicht als '***' maskiert."""
    app, tmp = _setup_app_with_mcp_file(
        {
            "server_mode": {"mode": "disabled", "auth_token": ""},
            "servers": {},
        }
    )
    try:
        handler = app.routes["GET /api/v1/mcp-servers"]
        result = await handler()
        assert result["auth_token"] == "", "Leeres auth_token sollte leer bleiben"
    finally:
        tmp.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_missing_auth_token_stays_empty() -> None:
    """Fehlendes auth_token ergibt leeren String, nicht '***'."""
    app, tmp = _setup_app_with_mcp_file(
        {
            "server_mode": {"mode": "disabled"},
            "servers": {},
        }
    )
    try:
        handler = app.routes["GET /api/v1/mcp-servers"]
        result = await handler()
        assert result["auth_token"] == ""
    finally:
        tmp.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_put_still_accepts_plaintext_token() -> None:
    """PUT /api/v1/mcp-servers muss auth_token im Klartext akzeptieren und speichern."""
    app, tmp = _setup_app_with_mcp_file(
        {
            "server_mode": {},
            "servers": {},
        }
    )
    try:
        handler = app.routes["PUT /api/v1/mcp-servers"]
        request = MagicMock()
        request.json = AsyncMock(
            return_value={
                "auth_token": "new-secret-token",
                "mode": "enabled",
            }
        )
        result = await handler(request=request)
        assert result["status"] == "ok"

        # Verify token was saved in plaintext to the file
        saved = yaml.safe_load(tmp.read_text(encoding="utf-8"))
        assert saved["server_mode"]["auth_token"] == "new-secret-token"
    finally:
        tmp.unlink(missing_ok=True)
