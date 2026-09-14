"""Tests for a2a/client.py and a2a/http_handler.py -- Coverage boost."""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cognithor.a2a.client import A2AClient, RemoteAgent
from cognithor.a2a.http_handler import A2AHTTPHandler
from cognithor.a2a.types import (
    A2A_CONTENT_TYPE,
    A2A_VERSION_HEADER,
    A2AAgentCapabilities,
    A2AAgentCard,
    A2ASkill,
    Message,
    MessageRole,
    TextPart,
)


def _make_mock_httpx(async_client_instance):
    """Create a mock httpx module with AsyncClient context-manager support."""
    mock_httpx = ModuleType("httpx")
    mock_ac = MagicMock()
    mock_ac.return_value = async_client_instance
    mock_httpx.AsyncClient = mock_ac  # type: ignore[attr-defined]
    return mock_httpx


def _make_async_client(
    *,
    get_return=None,
    get_side_effect=None,
    post_return=None,
    post_side_effect=None,
    stream_cm=None,
    stream_side_effect=None,
):
    """Create a mock AsyncClient instance with async context-manager support."""
    ac = AsyncMock()
    ac.__aenter__ = AsyncMock(return_value=ac)
    ac.__aexit__ = AsyncMock(return_value=False)
    if get_return is not None:
        ac.get = AsyncMock(return_value=get_return)
    if get_side_effect is not None:
        ac.get = AsyncMock(side_effect=get_side_effect)
    if post_return is not None:
        ac.post = AsyncMock(return_value=post_return)
    if post_side_effect is not None:
        ac.post = AsyncMock(side_effect=post_side_effect)
    if stream_cm is not None:
        ac.stream = MagicMock(return_value=stream_cm)
    if stream_side_effect is not None:
        ac.stream = MagicMock(side_effect=stream_side_effect)
    return ac


def _make_response(json_data):
    """Create a mock httpx Response."""
    resp = MagicMock()
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


# ============================================================================
# RemoteAgent Tests
# ============================================================================


class TestRemoteAgent:
    def test_name_with_card(self):
        card = A2AAgentCard(name="TestBot")
        agent = RemoteAgent("http://agent.local", card=card)
        assert agent.name == "TestBot"

    def test_name_without_card(self):
        agent = RemoteAgent("http://agent.local")
        assert agent.name == "http://agent.local"

    def test_a2a_url(self):
        agent = RemoteAgent("http://agent.local/")
        assert agent.a2a_url == "http://agent.local/a2a"

    def test_card_url(self):
        agent = RemoteAgent("http://agent.local")
        assert agent.card_url == "http://agent.local/.well-known/agent.json"

    def test_supports_streaming_false_no_card(self):
        agent = RemoteAgent("http://agent.local")
        assert agent.supports_streaming is False

    def test_supports_streaming_true(self):
        card = A2AAgentCard(capabilities=A2AAgentCapabilities(streaming=True))
        agent = RemoteAgent("http://agent.local", card=card)
        assert agent.supports_streaming is True

    def test_supports_streaming_false_with_card(self):
        card = A2AAgentCard(capabilities=A2AAgentCapabilities(streaming=False))
        agent = RemoteAgent("http://agent.local", card=card)
        assert agent.supports_streaming is False

    def test_to_dict_basic(self):
        agent = RemoteAgent("http://agent.local", auth_token="tok")
        agent.discovered_at = "2025-01-01"
        agent.last_contact = "2025-01-02"
        agent.request_count = 5
        agent.error_count = 1
        d = agent.to_dict()
        assert d["endpoint"] == "http://agent.local"
        assert d["request_count"] == 5
        assert d["error_count"] == 1
        assert d["has_card"] is False
        assert d["supports_streaming"] is False
        assert d["skills"] == []

    def test_to_dict_with_skills(self):
        card = A2AAgentCard(skills=[A2ASkill(id="s1", name="S1")])
        agent = RemoteAgent("http://agent.local", card=card)
        d = agent.to_dict()
        assert d["skills"] == ["s1"]
        assert d["has_card"] is True

    def test_trailing_slash_stripped(self):
        agent = RemoteAgent("http://agent.local///")
        assert agent.endpoint == "http://agent.local"


# ============================================================================
# A2AClient Management Tests
# ============================================================================


class TestA2AClientManagement:
    def test_register_remote(self):
        client = A2AClient()
        agent = client.register_remote("http://remote1.local", auth_token="t1")
        assert agent.endpoint == "http://remote1.local"
        assert agent.auth_token == "t1"
        assert agent.discovered_at != ""

    def test_unregister_existing(self):
        client = A2AClient()
        client.register_remote("http://remote1.local")
        assert client.unregister_remote("http://remote1.local") is True

    def test_unregister_nonexistent(self):
        client = A2AClient()
        assert client.unregister_remote("http://ghost.local") is False

    def test_unregister_with_trailing_slash(self):
        client = A2AClient()
        client.register_remote("http://remote1.local")
        assert client.unregister_remote("http://remote1.local/") is True

    def test_get_remote(self):
        client = A2AClient()
        client.register_remote("http://remote1.local")
        assert client.get_remote("http://remote1.local") is not None
        assert client.get_remote("http://ghost.local") is None
        assert client.get_remote("http://remote1.local/") is not None

    def test_list_remotes(self):
        client = A2AClient()
        client.register_remote("http://r1.local")
        client.register_remote("http://r2.local")
        assert len(client.list_remotes()) == 2

    def test_find_by_skill(self):
        client = A2AClient()
        card = A2AAgentCard(skills=[A2ASkill(id="code", name="Code")])
        client.register_remote("http://r1.local", card=card)
        client.register_remote("http://r2.local")
        assert len(client.find_by_skill("code")) == 1
        assert len(client.find_by_skill("missing")) == 0

    def test_find_by_tag(self):
        client = A2AClient()
        card = A2AAgentCard(tags=["jarvis", "dev"])
        client.register_remote("http://r1.local", card=card)
        assert len(client.find_by_tag("jarvis")) == 1
        assert len(client.find_by_tag("missing")) == 0

    def test_stats(self):
        client = A2AClient()
        client.register_remote("http://r1.local")
        s = client.stats()
        assert s["remote_agents"] == 1
        assert s["total_requests"] == 0
        assert len(s["agents"]) == 1


# ============================================================================
# A2AClient Discovery Tests
# ============================================================================


class TestA2AClientDiscovery:
    @pytest.mark.asyncio
    async def test_discover_success(self):
        client = A2AClient()
        card_data = A2AAgentCard(name="RemoteBot", skills=[]).to_dict()
        response = _make_response(card_data)
        ac = _make_async_client(get_return=response)
        mock_httpx = _make_mock_httpx(ac)

        with patch.dict(sys.modules, {"httpx": mock_httpx}):
            card = await client.discover("http://remote.local")

        assert card is not None
        assert card.name == "RemoteBot"
        assert client.get_remote("http://remote.local") is not None

    @pytest.mark.asyncio
    async def test_discover_updates_existing(self):
        client = A2AClient()
        client.register_remote("http://remote.local")
        card_data = A2AAgentCard(name="Updated").to_dict()
        response = _make_response(card_data)
        ac = _make_async_client(get_return=response)
        mock_httpx = _make_mock_httpx(ac)

        with patch.dict(sys.modules, {"httpx": mock_httpx}):
            card = await client.discover("http://remote.local")

        assert card is not None
        remote = client.get_remote("http://remote.local")
        assert remote.card is not None
        assert remote.last_contact != ""

    @pytest.mark.asyncio
    async def test_discover_httpx_not_installed(self):
        client = A2AClient()
        # Remove httpx from sys.modules to trigger ImportError
        saved = sys.modules.get("httpx")
        try:
            sys.modules["httpx"] = None  # causes ImportError on `import httpx`
            card = await client.discover("http://unreachable.local")
            assert card is None
        finally:
            if saved is not None:
                sys.modules["httpx"] = saved
            else:
                sys.modules.pop("httpx", None)

    @pytest.mark.asyncio
    async def test_discover_network_error(self):
        client = A2AClient()
        ac = _make_async_client(get_side_effect=Exception("Network error"))
        mock_httpx = _make_mock_httpx(ac)

        with patch.dict(sys.modules, {"httpx": mock_httpx}):
            card = await client.discover("http://broken.local")

        assert card is None


# ============================================================================
# A2AClient Task Operations Tests
# ============================================================================


class TestA2AClientTaskOps:
    @pytest.mark.asyncio
    async def test_send_message_success(self):
        client = A2AClient()
        client.register_remote("http://r.local")
        task_data = {
            "id": "t1",
            "contextId": "ctx1",
            "status": {"state": "completed", "timestamp": "2025-01-01T00:00:00Z"},
        }
        resp_data = {"jsonrpc": "2.0", "id": 1, "result": task_data}
        response = _make_response(resp_data)
        ac = _make_async_client(post_return=response)
        mock_httpx = _make_mock_httpx(ac)

        with patch.dict(sys.modules, {"httpx": mock_httpx}):
            task = await client.send_message("http://r.local", text="Hello")

        assert task is not None
        assert task.id == "t1"
        remote = client.get_remote("http://r.local")
        assert remote.request_count == 1

    @pytest.mark.asyncio
    async def test_send_message_with_message_object(self):
        client = A2AClient()
        task_data = {
            "id": "t2",
            "contextId": "ctx2",
            "status": {"state": "working"},
        }
        resp_data = {"jsonrpc": "2.0", "id": 1, "result": task_data}
        response = _make_response(resp_data)
        ac = _make_async_client(post_return=response)
        mock_httpx = _make_mock_httpx(ac)

        msg = Message(role=MessageRole.USER, parts=[TextPart(text="Hi")])
        with patch.dict(sys.modules, {"httpx": mock_httpx}):
            task = await client.send_message(
                "http://r.local",
                message=msg,
                task_id="t2",
                context_id="ctx2",
                metadata={"key": "val"},
            )

        assert task is not None

    @pytest.mark.asyncio
    async def test_send_message_rpc_error(self):
        client = A2AClient()
        client.register_remote("http://r.local")
        resp_data = {"jsonrpc": "2.0", "id": 1, "error": {"code": -32000, "message": "Boom"}}
        response = _make_response(resp_data)
        ac = _make_async_client(post_return=response)
        mock_httpx = _make_mock_httpx(ac)

        with patch.dict(sys.modules, {"httpx": mock_httpx}):
            task = await client.send_message("http://r.local", text="Hi")

        assert task is None
        remote = client.get_remote("http://r.local")
        assert remote.error_count == 1

    @pytest.mark.asyncio
    async def test_send_message_network_exception(self):
        client = A2AClient()
        client.register_remote("http://r.local")
        ac = _make_async_client(post_side_effect=Exception("Connection refused"))
        mock_httpx = _make_mock_httpx(ac)

        with patch.dict(sys.modules, {"httpx": mock_httpx}):
            task = await client.send_message("http://r.local", text="Hi")

        assert task is None
        assert client.get_remote("http://r.local").error_count == 1

    @pytest.mark.asyncio
    async def test_send_task_alias(self):
        client = A2AClient()
        with patch.object(
            client, "send_message", new_callable=AsyncMock, return_value=None
        ) as mock_send:
            await client.send_task("http://r.local", text="Hi")
            mock_send.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_task(self):
        client = A2AClient()
        task_data = {
            "id": "t1",
            "contextId": "ctx1",
            "status": {"state": "completed"},
        }
        resp_data = {"jsonrpc": "2.0", "id": 1, "result": task_data}
        response = _make_response(resp_data)
        ac = _make_async_client(post_return=response)
        mock_httpx = _make_mock_httpx(ac)

        with patch.dict(sys.modules, {"httpx": mock_httpx}):
            task = await client.get_task("http://r.local", "t1", history_length=5)

        assert task is not None
        assert task.id == "t1"

    @pytest.mark.asyncio
    async def test_list_tasks(self):
        client = A2AClient()
        result_data = {
            "tasks": [
                {"id": "t1", "contextId": "c1", "status": {"state": "completed"}},
                {"id": "t2", "contextId": "c2", "status": {"state": "working"}},
            ]
        }
        resp_data = {"jsonrpc": "2.0", "id": 1, "result": result_data}
        response = _make_response(resp_data)
        ac = _make_async_client(post_return=response)
        mock_httpx = _make_mock_httpx(ac)

        with patch.dict(sys.modules, {"httpx": mock_httpx}):
            tasks = await client.list_tasks("http://r.local", context_id="c1", state="completed")

        assert len(tasks) == 2

    @pytest.mark.asyncio
    async def test_list_tasks_empty(self):
        client = A2AClient()
        with patch.object(client, "_jsonrpc_call", new_callable=AsyncMock, return_value=None):
            tasks = await client.list_tasks("http://r.local")
        assert tasks == []

    @pytest.mark.asyncio
    async def test_cancel_task(self):
        client = A2AClient()
        task_data = {"id": "t1", "contextId": "c1", "status": {"state": "canceled"}}
        with patch.object(client, "_jsonrpc_call", new_callable=AsyncMock, return_value=task_data):
            task = await client.cancel_task("http://r.local", "t1")
        assert task is not None

    @pytest.mark.asyncio
    async def test_continue_task(self):
        client = A2AClient()
        with patch.object(
            client, "send_message", new_callable=AsyncMock, return_value=None
        ) as mock_send:
            await client.continue_task("http://r.local", "t1", "More text")
            mock_send.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_task_local_success(self):
        client = A2AClient()
        server = AsyncMock()
        server.dispatch = AsyncMock(
            return_value={
                "id": "t1",
                "contextId": "c1",
                "status": {"state": "completed"},
            }
        )
        task = await client.send_task_local(server, text="Hello")
        assert task is not None

    @pytest.mark.asyncio
    async def test_send_task_local_with_message(self):
        client = A2AClient()
        server = AsyncMock()
        server.dispatch = AsyncMock(
            return_value={
                "id": "t1",
                "contextId": "c1",
                "status": {"state": "completed"},
            }
        )
        msg = Message(role=MessageRole.USER, parts=[TextPart(text="Hi")])
        task = await client.send_task_local(server, message=msg, task_id="t1", context_id="c1")
        assert task is not None

    @pytest.mark.asyncio
    async def test_send_task_local_error(self):
        client = A2AClient()
        server = AsyncMock()
        server.dispatch = AsyncMock(return_value={"error": {"code": -1, "message": "Boom"}})
        task = await client.send_task_local(server, text="Fail")
        assert task is None

    @pytest.mark.asyncio
    async def test_jsonrpc_httpx_not_installed(self):
        """Test _jsonrpc_call when httpx is not installed."""
        client = A2AClient()
        saved = sys.modules.get("httpx")
        try:
            sys.modules["httpx"] = None  # causes ImportError
            result = await client._jsonrpc_call("http://r.local", "test/method", {})
            assert result is None
        finally:
            if saved is not None:
                sys.modules["httpx"] = saved
            else:
                sys.modules.pop("httpx", None)


# ============================================================================
# A2AClient _parse_task_response Tests
# ============================================================================


class TestParseTaskResponse:
    def test_parse_full_response(self):
        client = A2AClient()
        data = {
            "id": "t1",
            "contextId": "ctx1",
            "status": {
                "state": "completed",
                "message": {"role": "agent", "parts": [{"type": "text", "text": "Done"}]},
                "timestamp": "2025-01-01T00:00:00Z",
            },
            "messages": [{"role": "user", "parts": [{"type": "text", "text": "Hi"}]}],
            "artifacts": [{"parts": [{"type": "text", "text": "Result"}], "artifactId": "a1"}],
            "metadata": {"k": "v"},
        }
        task = client._parse_task_response(data)
        assert task is not None
        assert task.id == "t1"
        assert task.context_id == "ctx1"
        assert len(task.messages) == 1
        assert len(task.artifacts) == 1
        assert task.metadata == {"k": "v"}

    def test_parse_minimal_response(self):
        client = A2AClient()
        data = {"status": {"state": "submitted"}}
        task = client._parse_task_response(data)
        assert task is not None
        assert task.id == ""

    def test_parse_invalid_data(self):
        client = A2AClient()
        task = client._parse_task_response({"status": {"state": "INVALID_STATE"}})
        assert task is None


# ============================================================================
# A2AClient Streaming Tests
# ============================================================================


class TestA2AClientStreaming:
    @pytest.mark.asyncio
    async def test_send_message_stream_network_error(self):
        client = A2AClient()
        ac = _make_async_client(stream_side_effect=Exception("Connection error"))
        mock_httpx = _make_mock_httpx(ac)

        with patch.dict(sys.modules, {"httpx": mock_httpx}):
            events = []
            async for ev in client.send_message_stream("http://r.local", text="Hi"):
                events.append(ev)
        assert events == []

    @pytest.mark.asyncio
    async def test_send_message_stream_httpx_not_installed(self):
        client = A2AClient()
        saved = sys.modules.get("httpx")
        try:
            sys.modules["httpx"] = None
            events = []
            async for ev in client.send_message_stream("http://r.local", text="Hi"):
                events.append(ev)
            assert events == []
        finally:
            if saved is not None:
                sys.modules["httpx"] = saved
            else:
                sys.modules.pop("httpx", None)


# ============================================================================
# A2AClient _build_headers Tests
# ============================================================================


class TestBuildHeaders:
    def test_headers_without_auth(self):
        client = A2AClient()
        headers = client._build_headers()
        assert headers["Content-Type"] == A2A_CONTENT_TYPE
        assert A2A_VERSION_HEADER in headers

    def test_headers_with_auth(self):
        client = A2AClient()
        remote = RemoteAgent("http://r.local", auth_token="secret123")
        headers = client._build_headers(remote)
        assert headers["Authorization"] == "Bearer secret123"

    def test_headers_no_auth_token(self):
        client = A2AClient()
        remote = RemoteAgent("http://r.local")
        headers = client._build_headers(remote)
        assert "Authorization" not in headers


# ============================================================================
# A2AHTTPHandler Tests
# ============================================================================


class TestA2AHTTPHandler:
    def test_response_headers(self):
        adapter = MagicMock()
        handler = A2AHTTPHandler(adapter)
        headers = handler._response_headers()
        assert headers["Content-Type"] == A2A_CONTENT_TYPE
        assert A2A_VERSION_HEADER in headers

    def test_extract_token_bearer(self):
        adapter = MagicMock()
        handler = A2AHTTPHandler(adapter)
        assert handler._extract_token("Bearer mytoken") == "mytoken"

    def test_extract_token_none(self):
        adapter = MagicMock()
        handler = A2AHTTPHandler(adapter)
        assert handler._extract_token("") is None
        assert handler._extract_token("Basic abc") is None

    @pytest.mark.asyncio
    async def test_handle_agent_card(self):
        adapter = MagicMock()
        adapter.get_agent_card.return_value = {"name": "Jarvis"}
        handler = A2AHTTPHandler(adapter)
        result = await handler.handle_agent_card()
        assert result == {"name": "Jarvis"}

    @pytest.mark.asyncio
    async def test_handle_jsonrpc(self):
        adapter = AsyncMock()
        adapter.handle_a2a_request = AsyncMock(return_value={"result": "ok"})
        handler = A2AHTTPHandler(adapter)
        result = await handler.handle_jsonrpc(
            {"method": "test"}, auth_header="Bearer t", client_version="1.0"
        )
        assert result == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_handle_health_enabled(self):
        adapter = MagicMock()
        adapter.enabled = True
        adapter.stats.return_value = {"server": {"running": True}}
        handler = A2AHTTPHandler(adapter)
        result = await handler.handle_health()
        assert result["status"] == "ok"
        assert result["enabled"] is True

    @pytest.mark.asyncio
    async def test_handle_health_disabled(self):
        adapter = MagicMock()
        adapter.enabled = False
        adapter.stats.return_value = {"server": {"running": False}}
        handler = A2AHTTPHandler(adapter)
        result = await handler.handle_health()
        assert result["status"] == "disabled"

    def test_register_routes_no_starlette(self):
        adapter = MagicMock()
        handler = A2AHTTPHandler(adapter)
        app = MagicMock()
        with patch.dict(
            "sys.modules",
            {"starlette": None, "starlette.requests": None, "starlette.responses": None},
        ):
            handler.register_routes(app)

    @pytest.mark.asyncio
    async def test_start_standalone_no_aiohttp(self):
        adapter = MagicMock()
        handler = A2AHTTPHandler(adapter)
        handler._start_minimal_server = AsyncMock()
        with patch.dict("sys.modules", {"aiohttp": None, "aiohttp.web": None}):
            await handler.start_standalone("127.0.0.1", 9999)
