"""Tests for ToolsConfig and its integration into CognithorConfig."""

from __future__ import annotations

from cognithor.config import CognithorConfig, ToolsConfig


class TestToolsConfig:
    """Unit tests for the standalone ToolsConfig model."""

    def test_defaults(self) -> None:
        cfg = ToolsConfig()
        assert cfg.computer_use_enabled is False
        assert cfg.desktop_tools_enabled is False

    def test_enable_computer_use(self) -> None:
        cfg = ToolsConfig(computer_use_enabled=True)
        assert cfg.computer_use_enabled is True
        assert cfg.desktop_tools_enabled is False

    def test_enable_desktop_tools(self) -> None:
        cfg = ToolsConfig(desktop_tools_enabled=True)
        assert cfg.desktop_tools_enabled is True
        assert cfg.computer_use_enabled is False


class TestJarvisConfigToolsIntegration:
    """Integration tests: ToolsConfig wired into CognithorConfig."""

    def test_tools_section_exists(self) -> None:
        cfg = CognithorConfig()
        assert hasattr(cfg, "tools")
        assert isinstance(cfg.tools, ToolsConfig)

    def test_tools_defaults_in_jarvis_config(self) -> None:
        cfg = CognithorConfig()
        assert cfg.tools.computer_use_enabled is False
        assert cfg.tools.desktop_tools_enabled is False

    def test_tools_serialization(self) -> None:
        cfg = CognithorConfig()
        data = cfg.model_dump()
        assert "tools" in data
        assert data["tools"]["computer_use_enabled"] is False
        assert data["tools"]["desktop_tools_enabled"] is False


class TestGatekeeperBlocksDisabledTools:
    """Gatekeeper must block tools from disabled groups even if somehow registered."""

    COMPUTER_USE_TOOLS = {
        "computer_screenshot",
        "computer_click",
        "computer_type",
        "computer_hotkey",
        "computer_scroll",
        "computer_drag",
    }
    DESKTOP_TOOLS = {
        "get_clipboard",
        "set_clipboard",
        "screenshot_desktop",
        "screenshot_region",
    }

    def test_computer_use_blocked_when_disabled(self):
        from cognithor.core.gatekeeper import Gatekeeper

        config = CognithorConfig(tools=ToolsConfig(computer_use_enabled=False))
        gk = Gatekeeper(config)
        for tool in self.COMPUTER_USE_TOOLS:
            assert gk.is_tool_disabled(tool), f"{tool} should be disabled"

    def test_computer_use_allowed_when_enabled(self):
        from cognithor.core.gatekeeper import Gatekeeper

        config = CognithorConfig(tools=ToolsConfig(computer_use_enabled=True))
        gk = Gatekeeper(config)
        for tool in self.COMPUTER_USE_TOOLS:
            assert not gk.is_tool_disabled(tool), f"{tool} should be enabled"

    def test_desktop_tools_blocked_when_disabled(self):
        from cognithor.core.gatekeeper import Gatekeeper

        config = CognithorConfig(tools=ToolsConfig(desktop_tools_enabled=False))
        gk = Gatekeeper(config)
        for tool in self.DESKTOP_TOOLS:
            assert gk.is_tool_disabled(tool), f"{tool} should be disabled"

    def test_desktop_tools_allowed_when_enabled(self):
        from cognithor.core.gatekeeper import Gatekeeper

        config = CognithorConfig(tools=ToolsConfig(desktop_tools_enabled=True))
        gk = Gatekeeper(config)
        for tool in self.DESKTOP_TOOLS:
            assert not gk.is_tool_disabled(tool), f"{tool} should be enabled"
