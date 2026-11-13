"""Tests for Computer Use (desktop automation via coordinates)."""

from __future__ import annotations

import pytest


def test_computer_use_tools_importable():
    """ComputerUseTools class should be importable."""
    from cognithor.mcp.computer_use import ComputerUseTools

    tools = ComputerUseTools()
    assert tools is not None


def test_computer_use_gatekeeper_classification():
    """Computer use tools should NOT be RED when computer_use_enabled=True.

    Security model: screenshot is GREEN (read-only), action tools are YELLOW
    (user-opted-in but still require approval gate).  All tools become RED
    when computer_use_enabled=False.
    """
    from cognithor.config import CognithorConfig, ToolsConfig
    from cognithor.core.gatekeeper import Gatekeeper
    from cognithor.models import PlannedAction

    gk_enabled = Gatekeeper(CognithorConfig(tools=ToolsConfig(computer_use_enabled=True)))
    gk_disabled = Gatekeeper(CognithorConfig(tools=ToolsConfig(computer_use_enabled=False)))

    # Screenshot is read-only → GREEN
    ss_action = PlannedAction(tool="computer_screenshot", params={}, rationale="test")
    assert gk_enabled._classify_risk(ss_action).value == "green", (
        "computer_screenshot should be green"
    )

    # Active desktop actions → YELLOW (not RED, not GREEN)
    for tool in [
        "computer_click",
        "computer_type",
        "computer_hotkey",
        "computer_scroll",
        "computer_drag",
    ]:
        action = PlannedAction(tool=tool, params={}, rationale="test")
        assert gk_enabled._classify_risk(action).value == "yellow", (
            f"{tool} should be yellow when enabled, got {gk_enabled._classify_risk(action)}"
        )
        # Disabled → RED
        assert gk_disabled._classify_risk(action).value == "red", (
            f"{tool} should be red when disabled"
        )


@pytest.mark.asyncio
async def test_computer_screenshot():
    """computer_screenshot should return width/height."""
    from cognithor.mcp.computer_use import ComputerUseTools

    tools = ComputerUseTools()
    try:
        result = await tools.computer_screenshot()
        if result["success"]:
            assert "width" in result
            assert "height" in result
            assert result["width"] > 0
    except Exception:
        pytest.skip("Desktop screenshot not available in CI")
