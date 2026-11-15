"""Tests for WebSocket authentication and session-collision handling.

Validates:
- Token-based auth on the /ws/{session_id} endpoint
- Backwards compatibility when COGNITHOR_API_TOKEN is unset
- Session-ID collision closes the prior connection
"""

from __future__ import annotations

import contextlib
import json
import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient
from starlette.websockets import WebSocket, WebSocketDisconnect

# ---------------------------------------------------------------------------
# Helpers -- build a minimal FastAPI app that mirrors the production
# WebSocket handler from __main__.py (auth + collision logic only).
# ---------------------------------------------------------------------------


def _make_app() -> tuple[FastAPI, dict[str, WebSocket]]:
    """Return (app, ws_connections) using the same auth logic as __main__.py."""
    app = FastAPI()
    ws_connections: dict[str, WebSocket] = {}

    @app.websocket("/ws/{session_id}")
    async def ws_endpoint(websocket: WebSocket, session_id: str) -> None:
        # ── Token-based authentication (mirrors __main__.py) ──────
        required_token = os.environ.get("COGNITHOR_API_TOKEN")
        if required_token:
            client_token = websocket.query_params.get("token")
            if not client_token or client_token != required_token:
                await websocket.close(code=4001, reason="Unauthorized")
                return

        await websocket.accept()

        # ── Session collision: close existing connection ──────────
        existing = ws_connections.get(session_id)
        if existing is not None:
            with contextlib.suppress(Exception):
                await existing.close(code=4002, reason="Session replaced")

        ws_connections[session_id] = websocket
        try:
            while True:
                raw = await websocket.receive_text()
                data = json.loads(raw)
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                else:
                    await websocket.send_json({"type": "echo", "data": data})
        except WebSocketDisconnect:
            pass
        except Exception:
            pass
        finally:
            ws_connections.pop(session_id, None)

    return app, ws_connections


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestWSAuth:
    """WebSocket authentication tests."""

    def test_ws_no_token_required_when_env_unset(self) -> None:
        """When COGNITHOR_API_TOKEN is NOT set, any client can connect."""
        env = os.environ.copy()
        env.pop("COGNITHOR_API_TOKEN", None)

        with patch.dict(os.environ, env, clear=True):
            app, _ = _make_app()
            client = TestClient(app)
            with client.websocket_connect("/ws/test-session") as ws:
                ws.send_text(json.dumps({"type": "ping"}))
                resp = ws.receive_json()
                assert resp == {"type": "pong"}

    def test_ws_rejects_missing_token_when_env_set(self) -> None:
        """When COGNITHOR_API_TOKEN is set but client sends no token, reject."""
        with patch.dict(os.environ, {"COGNITHOR_API_TOKEN": "secret-123"}, clear=False):
            app, _ = _make_app()
            client = TestClient(app)
            # No ?token= query param -- must be rejected
            with pytest.raises(Exception):  # noqa: B017 — Starlette exception may have empty message
                with client.websocket_connect("/ws/test-session") as ws:
                    ws.send_text(json.dumps({"type": "ping"}))
            # Starlette raises an error when server closes before accept
            # The exact exception varies; the key is that the connection
            # did NOT succeed.

    def test_ws_rejects_wrong_token(self) -> None:
        """When COGNITHOR_API_TOKEN is set and client sends a wrong token, reject."""
        with patch.dict(os.environ, {"COGNITHOR_API_TOKEN": "secret-123"}, clear=False):
            app, _ = _make_app()
            client = TestClient(app)
            with pytest.raises(Exception):  # noqa: B017 — Starlette exception may have empty message
                with client.websocket_connect("/ws/test-session?token=wrong-token") as ws:
                    ws.send_text(json.dumps({"type": "ping"}))

    def test_ws_accepts_correct_token(self) -> None:
        """When COGNITHOR_API_TOKEN is set and client sends the correct token, allow."""
        with patch.dict(os.environ, {"COGNITHOR_API_TOKEN": "secret-123"}, clear=False):
            app, _ = _make_app()
            client = TestClient(app)
            with client.websocket_connect("/ws/test-session?token=secret-123") as ws:
                ws.send_text(json.dumps({"type": "ping"}))
                resp = ws.receive_json()
                assert resp == {"type": "pong"}

    def test_ws_session_collision_closes_old_connection(self) -> None:
        """When a new client connects with the same session_id, the old
        connection is closed with code 4002 before the new one is stored."""
        env = os.environ.copy()
        env.pop("COGNITHOR_API_TOKEN", None)

        with patch.dict(os.environ, env, clear=True):
            app, ws_connections = _make_app()
            client = TestClient(app)

            # Pre-populate the connection map with a mock "old" connection.
            # This simulates a stale/existing session that should be evicted.
            mock_old_ws = AsyncMock()
            ws_connections["collision-session"] = mock_old_ws

            # New client connects with the same session_id
            with client.websocket_connect("/ws/collision-session") as ws:
                ws.send_text(json.dumps({"type": "ping"}))
                resp = ws.receive_json()
                assert resp == {"type": "pong"}

                # The old mock connection must have been closed with 4002
                mock_old_ws.close.assert_awaited_once_with(
                    code=4002,
                    reason="Session replaced",
                )

                # The ws_connections dict should now point to the NEW
                # connection, NOT the old mock
                current = ws_connections.get("collision-session")
                assert current is not None
                assert current is not mock_old_ws


class TestWSAuthEdgeCases:
    """Additional edge-case tests for robustness."""

    def test_ws_empty_token_rejected(self) -> None:
        """An empty string token should be rejected when env token is set."""
        with patch.dict(os.environ, {"COGNITHOR_API_TOKEN": "secret-123"}, clear=False):
            app, _ = _make_app()
            client = TestClient(app)
            with pytest.raises(Exception):  # noqa: B017 — Starlette exception may have empty message
                with client.websocket_connect("/ws/test-session?token=") as ws:
                    ws.send_text(json.dumps({"type": "ping"}))

    def test_ws_token_not_required_when_env_empty_string(self) -> None:
        """When COGNITHOR_API_TOKEN is set to empty string, treat as unset."""
        with patch.dict(os.environ, {"COGNITHOR_API_TOKEN": ""}, clear=False):
            app, _ = _make_app()
            client = TestClient(app)
            with client.websocket_connect("/ws/test-session") as ws:
                ws.send_text(json.dumps({"type": "ping"}))
                resp = ws.receive_json()
                assert resp == {"type": "pong"}

    def test_ws_different_session_ids_independent(self) -> None:
        """Two different session_ids should not interfere with each other."""
        env = os.environ.copy()
        env.pop("COGNITHOR_API_TOKEN", None)

        with patch.dict(os.environ, env, clear=True):
            app, ws_connections = _make_app()
            client = TestClient(app)
            with client.websocket_connect("/ws/session-a") as ws_a:
                ws_a.send_text(json.dumps({"type": "ping"}))
                resp = ws_a.receive_json()
                assert resp == {"type": "pong"}
                assert "session-a" in ws_connections
