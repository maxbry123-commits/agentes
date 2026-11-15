"""Coverage-Tests fuer client.py -- fehlende Pfade abdecken."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

from cognithor.mcp.client import (
    JarvisMCPClient,
    ServerConnection,
    ToolCallResult,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def config(tmp_path: Path) -> MagicMock:
    cfg = MagicMock()
    cfg.mcp_config_file = tmp_path / "mcp" / "config.yaml"
    cfg.cognithor_home = tmp_path
    return cfg


@pytest.fixture
def client(config: MagicMock) -> JarvisMCPClient:
    return JarvisMCPClient(config)


class TestToolCallResult:
    def test_defaults(self) -> None:
        r = ToolCallResult()
        assert r.content == ""
        assert r.is_error is False


class TestServerConnection:
    def test_defaults(self) -> None:
        sc = ServerConnection(name="test", config=MagicMock())
        assert sc.connected is False
        assert sc.tools == {}


class TestRegisterBuiltinHandler:
    def test_register(self, client: JarvisMCPClient) -> None:
        client.register_builtin_handler("test_tool", lambda: "ok", description="Test tool")
        assert client.tool_count == 1
        assert "test_tool" in client.get_tool_list()

    def test_get_handler(self, client: JarvisMCPClient) -> None:
        def handler():
            return "ok"

        client.register_builtin_handler("test_tool", handler)
        assert client.get_handler("test_tool") is handler
        assert client.get_handler("nonexistent") is None


class TestCallTool:
    @pytest.mark.asyncio
    async def test_call_builtin_sync(self, client: JarvisMCPClient) -> None:
        client.register_builtin_handler("sync_tool", lambda x="": f"result: {x}")
        result = await client.call_tool("sync_tool", {"x": "hello"})
        assert "result: hello" in result.content
        assert not result.is_error

    @pytest.mark.asyncio
    async def test_call_builtin_async(self, client: JarvisMCPClient) -> None:
        async def async_handler(msg: str = "") -> str:
            return f"async: {msg}"

        client.register_builtin_handler("async_tool", async_handler)
        result = await client.call_tool("async_tool", {"msg": "test"})
        assert "async: test" in result.content
        assert not result.is_error

    @pytest.mark.asyncio
    async def test_call_builtin_exception(self, client: JarvisMCPClient) -> None:
        def bad_handler():
            raise RuntimeError("boom")

        client.register_builtin_handler("bad_tool", bad_handler)
        result = await client.call_tool("bad_tool", {})
        assert result.is_error
        assert "Builtin-Tool-Fehler" in result.content

    @pytest.mark.asyncio
    async def test_call_not_found(self, client: JarvisMCPClient) -> None:
        result = await client.call_tool("nonexistent", {})
        assert result.is_error
        assert "not_found" in result.content or "nicht gefunden" in result.content

    @pytest.mark.asyncio
    async def test_call_mcp_server_not_connected(self, client: JarvisMCPClient) -> None:
        from cognithor.models import MCPToolInfo

        client._tool_registry["remote_tool"] = MCPToolInfo(
            name="remote_tool",
            server="dead_server",
            description="",
            input_schema={},
        )
        result = await client.call_tool("remote_tool", {})
        assert result.is_error
        assert "not_connected" in result.content or "nicht verbunden" in result.content

    @pytest.mark.asyncio
    async def test_call_mcp_server_success(self, client: JarvisMCPClient) -> None:
        from cognithor.models import MCPToolInfo

        client._tool_registry["remote_tool"] = MCPToolInfo(
            name="remote_tool",
            server="srv1",
            description="",
            input_schema={},
        )
        mock_session = AsyncMock()
        mock_block = MagicMock()
        mock_block.text = "remote result"
        mock_result = MagicMock()
        mock_result.content = [mock_block]
        mock_result.isError = False
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        client._servers["srv1"] = ServerConnection(
            name="srv1",
            config=MagicMock(),
            session=mock_session,
            connected=True,
        )
        result = await client.call_tool("remote_tool", {"arg": "val"})
        assert not result.is_error
        assert "remote result" in result.content

    @pytest.mark.asyncio
    async def test_call_mcp_server_exception(self, client: JarvisMCPClient) -> None:
        from cognithor.models import MCPToolInfo

        client._tool_registry["err_tool"] = MCPToolInfo(
            name="err_tool",
            server="srv1",
            description="",
            input_schema={},
        )
        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(side_effect=RuntimeError("network error"))
        client._servers["srv1"] = ServerConnection(
            name="srv1",
            config=MagicMock(),
            session=mock_session,
            connected=True,
        )
        result = await client.call_tool("err_tool", {})
        assert result.is_error
        assert "Tool-Fehler" in result.content


class TestGetToolSchemas:
    def test_schemas(self, client: JarvisMCPClient) -> None:
        client.register_builtin_handler(
            "t1",
            lambda: None,
            description="Tool 1",
            input_schema={"type": "object"},
        )
        schemas = client.get_tool_schemas()
        assert "t1" in schemas
        assert schemas["t1"]["description"] == "Tool 1"


class TestProperties:
    def test_tool_count(self, client: JarvisMCPClient) -> None:
        assert client.tool_count == 0
        client.register_builtin_handler("t", lambda: None)
        assert client.tool_count == 1

    def test_server_count(self, client: JarvisMCPClient) -> None:
        assert client.server_count == 0


class TestLoadServerConfigs:
    def test_no_config_file(self, client: JarvisMCPClient) -> None:
        configs = client._load_server_configs()
        assert configs == {}

    def test_valid_config(self, client: JarvisMCPClient, tmp_path: Path) -> None:
        cfg_dir = tmp_path / "mcp"
        cfg_dir.mkdir(parents=True, exist_ok=True)
        cfg_file = cfg_dir / "config.yaml"
        cfg_file.write_text(
            "servers:\n  test_server:\n    command: python\n"
            "    args: [-m, test]\n    enabled: true\n"
            "    transport: stdio\n",
            encoding="utf-8",
        )
        client._config.mcp_config_file = cfg_file
        configs = client._load_server_configs()
        assert "test_server" in configs

    def test_config_too_large(self, client: JarvisMCPClient, tmp_path: Path) -> None:
        cfg_dir = tmp_path / "mcp"
        cfg_dir.mkdir(parents=True, exist_ok=True)
        cfg_file = cfg_dir / "config.yaml"
        cfg_file.write_text("x" * 2_000_000, encoding="utf-8")
        client._config.mcp_config_file = cfg_file
        configs = client._load_server_configs()
        assert configs == {}

    def test_invalid_yaml(self, client: JarvisMCPClient, tmp_path: Path) -> None:
        cfg_dir = tmp_path / "mcp"
        cfg_dir.mkdir(parents=True, exist_ok=True)
        cfg_file = cfg_dir / "config.yaml"
        cfg_file.write_text("not: [valid yaml", encoding="utf-8")
        client._config.mcp_config_file = cfg_file
        configs = client._load_server_configs()
        assert configs == {}


class TestDisconnectAll:
    @pytest.mark.asyncio
    async def test_disconnect_empty(self, client: JarvisMCPClient) -> None:
        await client.disconnect_all()
        assert client.server_count == 0

    @pytest.mark.asyncio
    async def test_disconnect_with_servers(self, client: JarvisMCPClient) -> None:
        mock_session = AsyncMock()
        mock_process = MagicMock()
        mock_process.returncode = None
        mock_process.terminate = MagicMock()
        mock_process.wait = AsyncMock()
        client._servers["srv"] = ServerConnection(
            name="srv",
            config=MagicMock(),
            session=mock_session,
            process=mock_process,
            connected=True,
        )
        await client.disconnect_all()
        assert client.server_count == 0


class TestSubscribeResource:
    @pytest.mark.asyncio
    async def test_subscribe_no_connection(self, client: JarvisMCPClient) -> None:
        result = await client.subscribe_resource("nonexistent", "jarvis://test", MagicMock())
        assert result is False

    @pytest.mark.asyncio
    async def test_subscribe_success(self, client: JarvisMCPClient) -> None:
        mock_session = AsyncMock()
        mock_session.subscribe_resource = AsyncMock()
        client._servers["srv"] = ServerConnection(
            name="srv",
            config=MagicMock(),
            session=mock_session,
            connected=True,
        )
        result = await client.subscribe_resource("srv", "jarvis://test", MagicMock())
        assert result is True

    @pytest.mark.asyncio
    async def test_subscribe_failure(self, client: JarvisMCPClient) -> None:
        mock_session = AsyncMock()
        mock_session.subscribe_resource = AsyncMock(side_effect=RuntimeError("fail"))
        client._servers["srv"] = ServerConnection(
            name="srv",
            config=MagicMock(),
            session=mock_session,
            connected=True,
        )
        result = await client.subscribe_resource("srv", "jarvis://test", MagicMock())
        assert result is False


class TestUnsubscribeResource:
    @pytest.mark.asyncio
    async def test_unsubscribe_no_connection(self, client: JarvisMCPClient) -> None:
        result = await client.unsubscribe_resource("nonexistent", "jarvis://test")
        assert result is False

    @pytest.mark.asyncio
    async def test_unsubscribe_success(self, client: JarvisMCPClient) -> None:
        mock_session = AsyncMock()
        mock_session.unsubscribe_resource = AsyncMock()
        client._servers["srv"] = ServerConnection(
            name="srv",
            config=MagicMock(),
            session=mock_session,
            connected=True,
        )
        client._subscriptions["srv"] = {"jarvis://test": [MagicMock()]}
        result = await client.unsubscribe_resource("srv", "jarvis://test")
        assert result is True

    @pytest.mark.asyncio
    async def test_unsubscribe_failure(self, client: JarvisMCPClient) -> None:
        mock_session = AsyncMock()
        mock_session.unsubscribe_resource = AsyncMock(side_effect=RuntimeError("fail"))
        client._servers["srv"] = ServerConnection(
            name="srv",
            config=MagicMock(),
            session=mock_session,
            connected=True,
        )
        result = await client.unsubscribe_resource("srv", "jarvis://test")
        assert result is False
