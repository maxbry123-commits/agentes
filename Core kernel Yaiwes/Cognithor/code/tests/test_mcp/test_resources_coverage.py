"""Coverage-Tests fuer resources.py -- fehlende Pfade abdecken."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from cognithor.mcp.resources import JarvisResourceProvider
from cognithor.mcp.server import JarvisMCPServer, MCPServerConfig, MCPToolDef


@pytest.fixture
def provider() -> JarvisResourceProvider:
    return JarvisResourceProvider()


@pytest.fixture
def provider_with_deps(tmp_path: Path) -> JarvisResourceProvider:
    config = MagicMock()
    config.cognithor_home = tmp_path
    memory = MagicMock()
    return JarvisResourceProvider(config=config, memory=memory)


@pytest.fixture
def server() -> JarvisMCPServer:
    return JarvisMCPServer(MCPServerConfig())


class TestRegisterAll:
    def test_registers_resources(
        self, provider: JarvisResourceProvider, server: JarvisMCPServer
    ) -> None:
        count = provider.register_all(server)
        assert count == 8  # 7 resources + 1 template

    def test_returns_count(
        self, provider_with_deps: JarvisResourceProvider, server: JarvisMCPServer
    ) -> None:
        count = provider_with_deps.register_all(server)
        assert count > 0


class TestReadCoreMemory:
    def test_no_memory(self, provider: JarvisResourceProvider) -> None:
        result = provider._read_core_memory()
        assert "nicht initialisiert" in result

    def test_with_content_attr(self, provider_with_deps: JarvisResourceProvider) -> None:
        core = MagicMock()
        core.content = "Core content here"
        provider_with_deps._memory.get_core_memory.return_value = core
        result = provider_with_deps._read_core_memory()
        assert result == "Core content here"

    def test_without_content_attr(self, provider_with_deps: JarvisResourceProvider) -> None:
        provider_with_deps._memory.get_core_memory.return_value = "plain string"
        result = provider_with_deps._read_core_memory()
        assert result == "plain string"

    def test_exception(self, provider_with_deps: JarvisResourceProvider) -> None:
        provider_with_deps._memory.get_core_memory.side_effect = RuntimeError("fail")
        result = provider_with_deps._read_core_memory()
        assert "Fehler" in result or "error" in result.lower()


class TestReadEpisodes:
    def test_no_memory(self, provider: JarvisResourceProvider) -> None:
        result = json.loads(provider._read_episodes())
        assert result["error"] == "Memory nicht initialisiert"

    def test_with_list_episodes(self, provider_with_deps: JarvisResourceProvider) -> None:
        ep1 = MagicMock()
        ep1.to_dict.return_value = {"topic": "test"}
        ep2 = {"topic": "dict_ep"}
        ep3 = "plain string"
        provider_with_deps._memory.get_recent_episodes.return_value = [ep1, ep2, ep3]
        result = json.loads(provider_with_deps._read_episodes())
        assert result["count"] == 3
        assert result["episodes"][0]["topic"] == "test"
        assert result["episodes"][1]["topic"] == "dict_ep"
        assert "plain string" in result["episodes"][2]["text"]

    def test_non_list_result(self, provider_with_deps: JarvisResourceProvider) -> None:
        provider_with_deps._memory.get_recent_episodes.return_value = "raw_string"
        result = json.loads(provider_with_deps._read_episodes())
        assert "raw_string" in result["episodes"]

    def test_exception(self, provider_with_deps: JarvisResourceProvider) -> None:
        provider_with_deps._memory.get_recent_episodes.side_effect = RuntimeError("fail")
        result = json.loads(provider_with_deps._read_episodes())
        assert "fail" in result["error"]


class TestReadMemoryStats:
    def test_no_memory(self, provider: JarvisResourceProvider) -> None:
        result = json.loads(provider._read_memory_stats())
        assert "error" in result

    def test_dict_stats(self, provider_with_deps: JarvisResourceProvider) -> None:
        provider_with_deps._memory.stats.return_value = {"chunks": 42}
        result = json.loads(provider_with_deps._read_memory_stats())
        assert result["chunks"] == 42

    def test_non_dict_stats(self, provider_with_deps: JarvisResourceProvider) -> None:
        provider_with_deps._memory.stats.return_value = "just a string"
        result = json.loads(provider_with_deps._read_memory_stats())
        assert "just a string" in result["stats"]

    def test_exception(self, provider_with_deps: JarvisResourceProvider) -> None:
        provider_with_deps._memory.stats.side_effect = RuntimeError("err")
        result = json.loads(provider_with_deps._read_memory_stats())
        assert "err" in result["error"]


class TestReadEntity:
    def test_no_entity_id(self, provider: JarvisResourceProvider) -> None:
        result = json.loads(provider._read_entity(uri=""))
        assert "not_found" in result["error"] or "gefunden" in result["error"].lower()

    def test_no_memory(self, provider: JarvisResourceProvider) -> None:
        result = json.loads(provider._read_entity(uri="jarvis://memory/entity/abc"))
        assert "not_found" in result["error"] or "gefunden" in result["error"].lower()

    def test_entity_with_to_dict(self, provider_with_deps: JarvisResourceProvider) -> None:
        entity = MagicMock()
        entity.to_dict.return_value = {"id": "abc", "name": "Test"}
        provider_with_deps._memory.get_entity.return_value = entity
        result = json.loads(provider_with_deps._read_entity(uri="jarvis://memory/entity/abc"))
        assert result["id"] == "abc"

    def test_entity_without_to_dict(self, provider_with_deps: JarvisResourceProvider) -> None:
        provider_with_deps._memory.get_entity.return_value = "plain entity"
        result = json.loads(provider_with_deps._read_entity(uri="jarvis://memory/entity/abc"))
        assert "plain entity" in result["entity"]

    def test_entity_not_found(self, provider_with_deps: JarvisResourceProvider) -> None:
        provider_with_deps._memory.get_entity.return_value = None
        result = json.loads(provider_with_deps._read_entity(uri="jarvis://memory/entity/abc"))
        assert "not_found" in result["error"] or "gefunden" in result["error"].lower()

    def test_entity_exception(self, provider_with_deps: JarvisResourceProvider) -> None:
        provider_with_deps._memory.get_entity.side_effect = RuntimeError("db err")
        result = json.loads(provider_with_deps._read_entity(uri="jarvis://memory/entity/abc"))
        assert "db err" in result["error"]


class TestReadStatus:
    def test_no_config(self, provider: JarvisResourceProvider) -> None:
        result = json.loads(provider._read_status())
        assert result["status"] == "running"
        assert result["config_loaded"] is False

    def test_with_config(self, provider_with_deps: JarvisResourceProvider) -> None:
        provider_with_deps._config.cognithor_home = Path("/test")
        provider_with_deps._config.default_model = "qwen3:32b"
        result = json.loads(provider_with_deps._read_status())
        assert result["config_loaded"] is True


class TestReadTools:
    def test_empty_server(self, provider: JarvisResourceProvider, server: JarvisMCPServer) -> None:
        result = json.loads(provider._read_tools(server))
        assert result["count"] == 0
        assert result["tools"] == []

    def test_with_tools(self, provider: JarvisResourceProvider, server: JarvisMCPServer) -> None:
        server.register_tool(
            MCPToolDef(
                name="test_tool",
                description="A test tool",
                input_schema={},
                handler=lambda: None,
            )
        )
        result = json.loads(provider._read_tools(server))
        assert result["count"] == 1
        assert result["tools"][0]["name"] == "test_tool"


class TestReadCapabilities:
    def test_returns_json(self, provider: JarvisResourceProvider) -> None:
        result = json.loads(provider._read_capabilities())
        assert result["agent_name"] == "Jarvis"
        assert "memory_system" in result["capabilities"]


class TestReadWorkspaceFiles:
    def test_no_config(self, provider: JarvisResourceProvider) -> None:
        result = json.loads(provider._read_workspace_files())
        assert "error" in result

    def test_no_workspace_dir(
        self, provider_with_deps: JarvisResourceProvider, tmp_path: Path
    ) -> None:
        provider_with_deps._config.cognithor_home = tmp_path
        # workspace dir does not exist
        result = json.loads(provider_with_deps._read_workspace_files())
        assert result["files"] == []

    def test_with_files(self, provider_with_deps: JarvisResourceProvider, tmp_path: Path) -> None:
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        (workspace / "file1.txt").write_text("hello", encoding="utf-8")
        sub = workspace / "subdir"
        sub.mkdir()
        (sub / "file2.md").write_text("world", encoding="utf-8")

        provider_with_deps._config.cognithor_home = tmp_path
        result = json.loads(provider_with_deps._read_workspace_files())
        assert result["count"] >= 2


class TestStats:
    def test_stats(self, provider_with_deps: JarvisResourceProvider) -> None:
        stats = provider_with_deps.stats()
        assert stats["memory_available"] is True
        assert stats["config_available"] is True

    def test_stats_no_deps(self, provider: JarvisResourceProvider) -> None:
        stats = provider.stats()
        assert stats["memory_available"] is False
        assert stats["config_available"] is False
