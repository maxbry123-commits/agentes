"""Tests for per-tool permission annotations (V6)."""

from __future__ import annotations

from unittest.mock import MagicMock

from cognithor.models import MCPToolInfo


class TestMCPToolInfoRiskLevel:
    def test_default_risk_level_empty(self):
        """Default risk_level is empty string (use Gatekeeper fallback)."""
        info = MCPToolInfo(name="test_tool", server="builtin")
        assert info.risk_level == ""

    def test_explicit_risk_level(self):
        info = MCPToolInfo(name="vault_delete", server="builtin", risk_level="red")
        assert info.risk_level == "red"

    def test_all_risk_levels_valid(self):
        for level in ("green", "yellow", "orange", "red"):
            info = MCPToolInfo(name="test", server="builtin", risk_level=level)
            assert info.risk_level == level


class TestGatekeeperToolRegistryIntegration:
    """Test that Gatekeeper reads risk_level from tool registry."""

    def _make_gatekeeper(self):
        """Create a minimal Gatekeeper with mocked config."""
        from cognithor.core.gatekeeper import Gatekeeper

        config = MagicMock()
        config.cognithor_home = MagicMock()
        config.cognithor_home.__truediv__ = MagicMock(return_value=MagicMock())
        config.logs_dir = MagicMock()
        config.logs_dir.__truediv__ = MagicMock(return_value=MagicMock())
        config.tools = None

        gk = Gatekeeper(config)
        return gk

    def _make_action(self, tool_name: str):
        """Create a minimal PlannedAction mock."""
        action = MagicMock()
        action.tool = tool_name
        action.params = {}
        action.rationale = "test"
        return action

    def test_annotated_green_tool(self):
        gk = self._make_gatekeeper()
        registry = {
            "read_file": MCPToolInfo(name="read_file", server="builtin", risk_level="green"),
        }
        gk.set_tool_registry(registry)

        from cognithor.core.gatekeeper import RiskLevel

        result = gk._classify_risk(self._make_action("read_file"))
        assert result == RiskLevel.GREEN

    def test_annotated_red_tool(self):
        gk = self._make_gatekeeper()
        registry = {
            "danger_tool": MCPToolInfo(name="danger_tool", server="builtin", risk_level="red"),
        }
        gk.set_tool_registry(registry)

        from cognithor.core.gatekeeper import RiskLevel

        result = gk._classify_risk(self._make_action("danger_tool"))
        assert result == RiskLevel.RED

    def test_unannotated_falls_back_to_hardcoded(self):
        """Empty risk_level → Gatekeeper uses hardcoded lists."""
        gk = self._make_gatekeeper()
        registry = {
            "read_file": MCPToolInfo(name="read_file", server="builtin", risk_level=""),
        }
        gk.set_tool_registry(registry)

        from cognithor.core.gatekeeper import RiskLevel

        # read_file is in the hardcoded GREEN list
        result = gk._classify_risk(self._make_action("read_file"))
        assert result == RiskLevel.GREEN

    def test_no_registry_uses_hardcoded(self):
        """Without tool registry, Gatekeeper uses hardcoded lists only."""
        gk = self._make_gatekeeper()
        # No set_tool_registry call

        from cognithor.core.gatekeeper import RiskLevel

        result = gk._classify_risk(self._make_action("read_file"))
        assert result == RiskLevel.GREEN

    def test_unknown_tool_without_annotation_is_orange(self):
        """Unknown tools default to ORANGE (fail-safe)."""
        gk = self._make_gatekeeper()
        registry = {
            "totally_new_tool": MCPToolInfo(
                name="totally_new_tool", server="builtin", risk_level=""
            ),
        }
        gk.set_tool_registry(registry)

        from cognithor.core.gatekeeper import RiskLevel

        result = gk._classify_risk(self._make_action("totally_new_tool"))
        assert result == RiskLevel.ORANGE

    def test_annotation_overrides_hardcoded(self):
        """Annotation takes priority over hardcoded list."""
        gk = self._make_gatekeeper()
        # exec_command is GREEN in hardcoded list, but annotate as orange
        registry = {
            "exec_command": MCPToolInfo(name="exec_command", server="builtin", risk_level="orange"),
        }
        gk.set_tool_registry(registry)

        from cognithor.core.gatekeeper import RiskLevel

        result = gk._classify_risk(self._make_action("exec_command"))
        assert result == RiskLevel.ORANGE
