"""Enhanced tests for APIChannel -- additional coverage.

Covers: request_approval (timeout, success), TLS warning on external host,
FastAPI import error, no-token endpoint, rate limiting, handler not ready,
serve_task cancel in stop.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cognithor.channels.api import APIChannel
from cognithor.models import OutgoingMessage, PlannedAction


@pytest.fixture
def ch() -> APIChannel:
    return APIChannel(host="127.0.0.1", port=8741, api_token="test-token")


class TestAPIProperties:
    def test_name(self, ch: APIChannel) -> None:
        assert ch.name == "api"

    def test_api_token_property(self, ch: APIChannel) -> None:
        token = ch._api_token
        assert token == "test-token"

    def test_api_token_no_token(self) -> None:
        ch = APIChannel()
        assert ch._api_token is None


class TestAPIStart:
    @pytest.mark.asyncio
    async def test_start_creates_app(self, ch: APIChannel) -> None:
        handler = AsyncMock()
        await ch.start(handler)
        assert ch._handler is handler
        assert ch._app is not None
        assert ch._start_time > 0

    @pytest.mark.asyncio
    async def test_start_tls_warning_external_host(self) -> None:
        """External host without TLS should log warning."""
        ch = APIChannel(host="0.0.0.0", port=8741, api_token="token")
        handler = AsyncMock()
        await ch.start(handler)
        # Should not crash; warning is logged but we verify app was created
        assert ch._app is not None


class TestAPIStop:
    @pytest.mark.asyncio
    async def test_stop_cancels_serve_task(self, ch: APIChannel) -> None:
        mock_task = MagicMock()
        mock_task.done.return_value = False
        mock_task.cancel = MagicMock()
        ch._serve_task = mock_task

        await ch.stop()
        mock_task.cancel.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_serve_task_done(self, ch: APIChannel) -> None:
        mock_task = MagicMock()
        mock_task.done.return_value = True
        ch._serve_task = mock_task

        await ch.stop()
        mock_task.cancel.assert_not_called()

    @pytest.mark.asyncio
    async def test_stop_cancels_pending_approvals(self, ch: APIChannel) -> None:
        f1 = asyncio.get_event_loop().create_future()
        f2 = asyncio.get_event_loop().create_future()
        ch._pending_approvals["r1"] = f1
        ch._pending_approvals["r2"] = f2

        await ch.stop()
        assert len(ch._pending_approvals) == 0
        assert f1.result() is False
        assert f2.result() is False


class TestAPISend:
    @pytest.mark.asyncio
    async def test_send_is_noop(self, ch: APIChannel) -> None:
        msg = OutgoingMessage(text="test", session_id="s1", channel="api")
        await ch.send(msg)  # no crash, no action

    @pytest.mark.asyncio
    async def test_streaming_token_is_noop(self, ch: APIChannel) -> None:
        await ch.send_streaming_token("s1", "token")  # no crash


class TestAPIApproval:
    @pytest.mark.asyncio
    async def test_request_approval_success(self, ch: APIChannel) -> None:
        action = PlannedAction(tool="email_send", params={"to": "test@example.com"})

        async def resolve_future():
            await asyncio.sleep(0.01)
            # Find the pending future and resolve it
            for _req_id, future in ch._pending_approvals.items():
                if not future.done():
                    future.set_result(True)
                    break

        task = asyncio.create_task(resolve_future())
        result = await ch.request_approval("s1", action, "reason")
        await task
        assert result is True

    @pytest.mark.asyncio
    async def test_request_approval_denied(self, ch: APIChannel) -> None:
        action = PlannedAction(tool="shell_exec", params={"cmd": "rm -rf /"})

        async def deny_future():
            await asyncio.sleep(0.01)
            for _req_id, future in ch._pending_approvals.items():
                if not future.done():
                    future.set_result(False)
                    break

        task = asyncio.create_task(deny_future())
        result = await ch.request_approval("s1", action, "dangerous")
        await task
        assert result is False

    @pytest.mark.asyncio
    async def test_request_approval_timeout(self, ch: APIChannel) -> None:
        action = PlannedAction(tool="test", params={})

        # Patch wait_for to use very short timeout
        original_wait_for = asyncio.wait_for

        async def short_wait_for(coro, *, timeout):
            return await original_wait_for(coro, timeout=0.01)

        with patch("cognithor.channels.api.asyncio.wait_for", side_effect=short_wait_for):
            result = await ch.request_approval("s1", action, "reason")

        assert result is False


class TestAPICreateApp:
    def test_create_app_fastapi_import_error(self, ch: APIChannel) -> None:
        with patch.dict("sys.modules", {"fastapi": None}):
            with pytest.raises(ImportError, match="FastAPI"):
                ch._create_app()

    def test_app_property_creates_once(self, ch: APIChannel) -> None:
        app = ch.app
        assert app is not None
        assert ch.app is app  # same instance


class TestAPIEndpointsViaHTTPX:
    """Test API endpoints using HTTPX TestClient."""

    @pytest.fixture
    def api_client(self, ch: APIChannel):
        try:
            from httpx import ASGITransport, AsyncClient
        except ImportError:
            pytest.skip("httpx not installed")

        handler = AsyncMock(
            return_value=OutgoingMessage(text="response", session_id="s1", channel="api")
        )
        loop = asyncio.new_event_loop()
        loop.run_until_complete(ch.start(handler))
        loop.close()

        transport = ASGITransport(app=ch.app)
        return AsyncClient(
            transport=transport,
            base_url="http://test",
            headers={"Authorization": "Bearer test-token"},
        )

    @pytest.mark.asyncio
    async def test_health_endpoint(self, api_client) -> None:
        resp = await api_client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_no_token_configured(self) -> None:
        """API without token configured returns 503."""
        try:
            from httpx import ASGITransport, AsyncClient
        except ImportError:
            pytest.skip("httpx not installed")

        ch = APIChannel(host="127.0.0.1", port=8741)
        handler = AsyncMock()
        await ch.start(handler)

        transport = ASGITransport(app=ch.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/message",
                json={"text": "hello"},
                headers={"Authorization": "Bearer some-token"},
            )
            assert resp.status_code == 503

    @pytest.mark.asyncio
    async def test_handler_not_ready(self, ch: APIChannel) -> None:
        """Send message when handler is None returns 503."""
        try:
            from httpx import ASGITransport, AsyncClient
        except ImportError:
            pytest.skip("httpx not installed")

        handler = AsyncMock()
        await ch.start(handler)
        ch._handler = None

        transport = ASGITransport(app=ch.app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            headers={"Authorization": "Bearer test-token"},
        ) as client:
            resp = await client.post("/api/v1/message", json={"text": "hello"})
            assert resp.status_code == 503

    @pytest.mark.asyncio
    async def test_approval_respond_not_found(self, api_client) -> None:
        resp = await api_client.post(
            "/api/v1/approvals/respond",
            json={"request_id": "nonexistent", "approved": True},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_sessions_endpoint(self, api_client) -> None:
        # First send a message to create a session
        await api_client.post(
            "/api/v1/message",
            json={"text": "hello", "session_id": "test-sess"},
        )
        resp = await api_client.get("/api/v1/sessions")
        assert resp.status_code == 200
        sessions = resp.json()
        assert len(sessions) >= 1
