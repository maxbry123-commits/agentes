"""Coverage-Tests fuer bridge.py -- fehlende Pfade abdecken."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

from cognithor.mcp.bridge import (
    MCPBridge,
    _build_annotations,
)
from cognithor.mcp.server import MCPServerMode, ToolAnnotationKey

if TYPE_CHECKING:
    from pathlib import Path

# ============================================================================
# _build_annotations
# ============================================================================


class TestBuildAnnotations:
    def test_read_only(self) -> None:
        ann = _build_annotations("read_file")
        assert ann.get(ToolAnnotationKey.READ_ONLY_HINT.value) is True
        assert ann.get(ToolAnnotationKey.IDEMPOTENT_HINT.value) is True

    def test_destructive(self) -> None:
        ann = _build_annotations("write_file")
        assert ann.get(ToolAnnotationKey.DESTRUCTIVE_HINT.value) is True

    def test_unknown_tool(self) -> None:
        ann = _build_annotations("unknown_tool_name")
        assert ann == {}

    def test_idempotent_only(self) -> None:
        ann = _build_annotations("browse_screenshot")
        assert ann.get(ToolAnnotationKey.READ_ONLY_HINT.value) is True
        assert ann.get(ToolAnnotationKey.IDEMPOTENT_HINT.value) is True


# ============================================================================
# MCPBridge
# ============================================================================


@pytest.fixture
def config(tmp_path: Path) -> MagicMock:
    cfg = MagicMock()
    cfg.mcp_config_file = tmp_path / "mcp" / "config.yaml"
    cfg.cognithor_home = tmp_path
    cfg.owner_name = "TestOwner"
    return cfg


@pytest.fixture
def bridge(config: MagicMock) -> MCPBridge:
    return MCPBridge(config)


class TestMCPBridgeInit:
    def test_defaults(self, bridge: MCPBridge) -> None:
        assert bridge.enabled is False
        assert bridge.server is None
        assert bridge.discovery is None


class TestMCPBridgeSetup:
    def test_disabled_mode(self, bridge: MCPBridge) -> None:
        mcp_client = MagicMock()
        # _load_server_config returns disabled config by default (no file)
        result = bridge.setup(mcp_client)
        assert result is False
        assert bridge.enabled is False

    def test_enabled_mode(self, bridge: MCPBridge, config: MagicMock, tmp_path: Path) -> None:
        # Create a config file with http mode
        cfg_dir = tmp_path / "mcp"
        cfg_dir.mkdir(parents=True, exist_ok=True)
        cfg_file = cfg_dir / "config.yaml"
        cfg_file.write_text(
            "server_mode:\n  mode: http\n  http_host: 127.0.0.1\n  http_port: 9999\n",
            encoding="utf-8",
        )
        config.mcp_config_file = cfg_file

        mcp_client = MagicMock()
        mcp_client.get_tool_schemas.return_value = {
            "read_file": {"description": "Read file", "inputSchema": {}},
        }
        mcp_client._builtin_handlers = {"read_file": lambda: None}
        mcp_client.get_tool_list.return_value = ["read_file"]

        result = bridge.setup(mcp_client)
        assert result is True
        assert bridge.enabled is True
        assert bridge.server is not None


class TestMCPBridgeStartStop:
    @pytest.mark.asyncio
    async def test_start_disabled(self, bridge: MCPBridge) -> None:
        await bridge.start()  # should not raise

    @pytest.mark.asyncio
    async def test_stop_no_server(self, bridge: MCPBridge) -> None:
        await bridge.stop()  # should not raise

    @pytest.mark.asyncio
    async def test_start_enabled(self, bridge: MCPBridge) -> None:
        mock_server = AsyncMock()
        bridge._server = mock_server
        bridge._enabled = True
        await bridge.start()
        mock_server.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_with_server(self, bridge: MCPBridge) -> None:
        mock_server = AsyncMock()
        bridge._server = mock_server
        await bridge.stop()
        mock_server.stop.assert_called_once()


class TestHandleMcpRequest:
    @pytest.mark.asyncio
    async def test_no_server(self, bridge: MCPBridge) -> None:
        result = await bridge.handle_mcp_request({"jsonrpc": "2.0"})
        assert result["error"]["code"] == -32000

    @pytest.mark.asyncio
    async def test_with_server(self, bridge: MCPBridge) -> None:
        mock_server = AsyncMock()
        mock_server.handle_http_request = AsyncMock(return_value={"jsonrpc": "2.0", "result": "ok"})
        bridge._server = mock_server
        await bridge.handle_mcp_request(
            {"jsonrpc": "2.0", "method": "ping"},
            auth_header="Bearer test-token",
        )
        mock_server.handle_http_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_bearer(self, bridge: MCPBridge) -> None:
        mock_server = AsyncMock()
        mock_server.handle_http_request = AsyncMock(return_value={})
        bridge._server = mock_server
        await bridge.handle_mcp_request({}, auth_header="Basic xxx")
        call_kwargs = mock_server.handle_http_request.call_args
        assert call_kwargs.kwargs.get("auth_token") is None


class TestGetAgentCard:
    def test_no_discovery(self, bridge: MCPBridge) -> None:
        result = bridge.get_agent_card()
        assert "error" in result

    def test_with_discovery(self, bridge: MCPBridge) -> None:
        mock_disc = MagicMock()
        mock_disc.get_card.return_value = {"name": "Jarvis"}
        bridge._discovery = mock_disc
        result = bridge.get_agent_card()
        assert result["name"] == "Jarvis"


class TestGetHealth:
    def test_no_discovery(self, bridge: MCPBridge) -> None:
        result = bridge.get_health()
        assert result["status"] == "disabled"

    def test_with_discovery(self, bridge: MCPBridge) -> None:
        mock_disc = MagicMock()
        mock_disc.health.return_value = {"status": "ok"}
        bridge._discovery = mock_disc
        result = bridge.get_health()
        assert result["status"] == "ok"


class TestBridgeStats:
    def test_disabled(self, bridge: MCPBridge) -> None:
        stats = bridge.stats()
        assert stats["enabled"] is False

    def test_with_components(self, bridge: MCPBridge) -> None:
        bridge._enabled = True
        bridge._setup_time = 0.5
        bridge._server = MagicMock()
        bridge._server.stats.return_value = {"tools": 3}
        bridge._resource_provider = MagicMock()
        bridge._resource_provider.stats.return_value = {"registered_resources": 8}
        bridge._prompt_provider = MagicMock()
        bridge._prompt_provider.stats.return_value = {"registered_prompts": 2}
        bridge._discovery = MagicMock()
        bridge._discovery.stats.return_value = {"card_requests": 0}

        stats = bridge.stats()
        assert stats["enabled"] is True
        assert "server" in stats
        assert "resources" in stats
        assert "prompts" in stats
        assert "discovery" in stats


class TestLoadServerConfig:
    def test_no_config_file(self, bridge: MCPBridge) -> None:
        cfg = bridge._load_server_config()
        assert cfg.mode == MCPServerMode.DISABLED

    def test_invalid_mode(self, bridge: MCPBridge, config: MagicMock, tmp_path: Path) -> None:
        cfg_dir = tmp_path / "mcp"
        cfg_dir.mkdir(parents=True, exist_ok=True)
        cfg_file = cfg_dir / "config.yaml"
        cfg_file.write_text(
            "server_mode:\n  mode: invalid_mode\n",
            encoding="utf-8",
        )
        config.mcp_config_file = cfg_file
        cfg = bridge._load_server_config()
        assert cfg.mode == MCPServerMode.DISABLED

    def test_yaml_error(self, bridge: MCPBridge, config: MagicMock, tmp_path: Path) -> None:
        cfg_dir = tmp_path / "mcp"
        cfg_dir.mkdir(parents=True, exist_ok=True)
        cfg_file = cfg_dir / "config.yaml"
        cfg_file.write_text("not: [valid yaml", encoding="utf-8")
        config.mcp_config_file = cfg_file
        cfg = bridge._load_server_config()
        assert cfg.mode == MCPServerMode.DISABLED
