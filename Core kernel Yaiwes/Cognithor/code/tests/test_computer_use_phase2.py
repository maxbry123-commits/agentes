"""Tests for Computer Use Phase 2 — vision-guided clicking + change detection."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cognithor.mcp.computer_use import ComputerUseTools


class MockVisionResult:
    def __init__(self, description="Desktop", elements=None, success=True, error=""):
        self.description = description
        self.elements = elements or []
        self.success = success
        self.error = error


@pytest.fixture
def tools():
    vision = AsyncMock()
    vision.analyze_desktop = AsyncMock(
        return_value=MockVisionResult(
            description="Desktop with login form",
            elements=[
                {
                    "name": "Login Button",
                    "type": "button",
                    "x": 400,
                    "y": 300,
                    "clickable": True,
                    "text": "Login",
                },
                {
                    "name": "Username Field",
                    "type": "textfield",
                    "x": 400,
                    "y": 200,
                    "clickable": True,
                    "text": "",
                },
                {"name": "Logo", "type": "icon", "x": 100, "y": 50, "clickable": False, "text": ""},
            ],
        )
    )
    return ComputerUseTools(vision_analyzer=vision)


class TestClickElement:
    @pytest.mark.asyncio
    async def test_click_by_name(self, tools):
        with patch(
            "cognithor.mcp.computer_use._take_screenshot_b64",
            return_value=("base64data", 1920, 1080, 1.0),
        ):
            with patch("cognithor.mcp.computer_use._get_pyautogui") as mock_gui:
                mock_gui.return_value.click = MagicMock()
                result = await tools.computer_click_element("Login Button")
                assert result["success"] is True
                assert result["matched_element"] == "Login Button"
                assert result["match_score"] >= 80

    @pytest.mark.asyncio
    async def test_click_by_partial_description(self, tools):
        with patch(
            "cognithor.mcp.computer_use._take_screenshot_b64",
            return_value=("base64data", 1920, 1080, 1.0),
        ):
            with patch("cognithor.mcp.computer_use._get_pyautogui") as mock_gui:
                mock_gui.return_value.click = MagicMock()
                result = await tools.computer_click_element("login")
                assert result["success"] is True
                assert "Login" in result["matched_element"]

    @pytest.mark.asyncio
    async def test_click_by_text(self, tools):
        with patch(
            "cognithor.mcp.computer_use._take_screenshot_b64",
            return_value=("base64data", 1920, 1080, 1.0),
        ):
            with patch("cognithor.mcp.computer_use._get_pyautogui") as mock_gui:
                mock_gui.return_value.click = MagicMock()
                result = await tools.computer_click_element("Login")
                assert result["success"] is True

    @pytest.mark.asyncio
    async def test_no_match(self, tools):
        with patch(
            "cognithor.mcp.computer_use._take_screenshot_b64",
            return_value=("base64data", 1920, 1080, 1.0),
        ):
            result = await tools.computer_click_element("nonexistent element xyz")
            assert result["success"] is False
            assert "No element matching" in result["error"]
            assert "Available elements" in result["error"]

    @pytest.mark.asyncio
    async def test_no_elements_detected(self, tools):
        tools._vision.analyze_desktop = AsyncMock(return_value=MockVisionResult(elements=[]))
        with patch(
            "cognithor.mcp.computer_use._take_screenshot_b64",
            return_value=("base64data", 1920, 1080, 1.0),
        ):
            result = await tools.computer_click_element("anything")
            assert result["success"] is False
            assert "No UI elements" in result["error"]

    @pytest.mark.asyncio
    async def test_prefers_clickable(self, tools):
        tools._vision.analyze_desktop = AsyncMock(
            return_value=MockVisionResult(
                elements=[
                    {
                        "name": "Save",
                        "type": "icon",
                        "x": 100,
                        "y": 100,
                        "clickable": False,
                        "text": "Save",
                    },
                    {
                        "name": "Save",
                        "type": "button",
                        "x": 200,
                        "y": 200,
                        "clickable": True,
                        "text": "Save",
                    },
                ],
            )
        )
        with patch(
            "cognithor.mcp.computer_use._take_screenshot_b64",
            return_value=("base64data", 1920, 1080, 1.0),
        ):
            with patch("cognithor.mcp.computer_use._get_pyautogui") as mock_gui:
                mock_gui.return_value.click = MagicMock()
                result = await tools.computer_click_element("Save")
                assert result["success"] is True
                # Should click the clickable button (200,200), not the icon (100,100)
                assert result["x"] == 200


class TestWaitForChange:
    @pytest.mark.asyncio
    async def test_detects_change(self, tools):
        tools._last_screenshot_hash = "old_hash"
        with patch(
            "cognithor.mcp.computer_use._take_screenshot_b64",
            return_value=("new_data", 1920, 1080, 1.0),
        ):
            result = await tools.computer_wait_for_change(timeout_ms=1000)
            assert result["changed"] is True

    @pytest.mark.asyncio
    async def test_no_change_timeout(self, tools):
        tools._last_screenshot_hash = "some_hash"
        # Return same data every time → same hash
        with patch("cognithor.mcp.computer_use._take_screenshot_b64") as mock_ss:
            # MD5 of "same_data" will be consistent
            mock_ss.return_value = ("same_data", 1920, 1080, 1.0)
            tools._last_screenshot_hash = __import__("hashlib").md5(b"same_data").hexdigest()
            result = await tools.computer_wait_for_change(timeout_ms=500)
            assert result["changed"] is False

    @pytest.mark.asyncio
    async def test_no_previous_screenshot(self, tools):
        tools._last_screenshot_hash = ""
        result = await tools.computer_wait_for_change()
        assert result["changed"] is True
        assert "No previous" in result["detail"]
