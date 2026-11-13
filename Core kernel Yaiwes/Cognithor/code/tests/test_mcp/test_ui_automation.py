"""Tests for UIAutomationProvider — Windows Accessibility Tree integration."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from cognithor.mcp.ui_automation import UIAutomationProvider


class TestUIAutomationProvider:
    def test_import_and_instantiate(self):
        provider = UIAutomationProvider()
        assert provider is not None

    def test_element_format_has_required_keys(self):
        provider = UIAutomationProvider()
        mock_elem = MagicMock()
        mock_elem.window_text.return_value = "OK"
        mock_elem.element_info.control_type = "Button"
        mock_elem.element_info.visible = True
        mock_elem.is_enabled.return_value = True
        mock_elem.rectangle.return_value = MagicMock(left=100, top=200, right=200, bottom=230)

        elem_dict = provider._element_to_dict(mock_elem)
        assert elem_dict is not None
        assert elem_dict["name"] == "OK"
        assert elem_dict["type"] == "Button"
        assert elem_dict["x"] == 150
        assert elem_dict["y"] == 215
        assert elem_dict["w"] == 100
        assert elem_dict["h"] == 30
        assert elem_dict["clickable"] is True
        assert elem_dict["source"] == "uia"

    def test_excluded_control_types_filtered(self):
        provider = UIAutomationProvider()
        assert not provider._is_interactive_type("Pane")
        assert not provider._is_interactive_type("Group")
        assert not provider._is_interactive_type("ScrollViewer")
        assert not provider._is_interactive_type("Text")
        assert not provider._is_interactive_type("Image")
        assert not provider._is_interactive_type("Separator")

    def test_included_control_types_pass(self):
        provider = UIAutomationProvider()
        assert provider._is_interactive_type("Button")
        assert provider._is_interactive_type("Edit")
        assert provider._is_interactive_type("MenuItem")
        assert provider._is_interactive_type("ListItem")
        assert provider._is_interactive_type("CheckBox")
        assert provider._is_interactive_type("ComboBox")
        assert provider._is_interactive_type("Hyperlink")
        assert provider._is_interactive_type("TabItem")
        assert provider._is_interactive_type("RadioButton")
        assert provider._is_interactive_type("TreeItem")

    def test_max_elements_cap(self):
        provider = UIAutomationProvider()
        elements = [
            {
                "name": f"btn{i}",
                "type": "Button",
                "x": i * 10,
                "y": 100,
                "w": 50,
                "h": 20,
                "clickable": True,
                "text": "",
                "source": "uia",
            }
            for i in range(50)
        ]
        capped = provider._cap_and_sort(elements)
        assert len(capped) <= 30

    def test_sorting_top_left_to_bottom_right(self):
        provider = UIAutomationProvider()
        elements = [
            {
                "name": "C",
                "x": 500,
                "y": 100,
                "type": "Button",
                "w": 50,
                "h": 20,
                "clickable": True,
                "text": "",
                "source": "uia",
            },
            {
                "name": "A",
                "x": 100,
                "y": 100,
                "type": "Button",
                "w": 50,
                "h": 20,
                "clickable": True,
                "text": "",
                "source": "uia",
            },
            {
                "name": "B",
                "x": 200,
                "y": 300,
                "type": "Button",
                "w": 50,
                "h": 20,
                "clickable": True,
                "text": "",
                "source": "uia",
            },
        ]
        sorted_elems = provider._cap_and_sort(elements)
        assert sorted_elems[0]["name"] == "A"
        assert sorted_elems[1]["name"] == "C"
        assert sorted_elems[2]["name"] == "B"

    def test_graceful_degradation_no_pywinauto(self):
        provider = UIAutomationProvider()
        provider._pywinauto_available = False
        result = provider.get_focused_window_elements()
        assert result == []

    def test_graceful_degradation_exception(self):
        provider = UIAutomationProvider()
        with patch.object(
            provider, "_get_foreground_window", side_effect=RuntimeError("COM error")
        ):
            result = provider.get_focused_window_elements()
            assert result == []

    def test_zero_size_elements_excluded(self):
        provider = UIAutomationProvider()
        mock_elem = MagicMock()
        mock_elem.window_text.return_value = "Hidden"
        mock_elem.element_info.control_type = "Button"
        mock_elem.element_info.visible = True
        mock_elem.is_enabled.return_value = True
        mock_elem.rectangle.return_value = MagicMock(left=100, top=200, right=100, bottom=200)
        elem_dict = provider._element_to_dict(mock_elem)
        assert elem_dict is None

    def test_long_name_truncated(self):
        provider = UIAutomationProvider()
        mock_elem = MagicMock()
        mock_elem.window_text.return_value = "A" * 100
        mock_elem.element_info.control_type = "Button"
        mock_elem.is_enabled.return_value = True
        mock_elem.rectangle.return_value = MagicMock(left=0, top=0, right=100, bottom=30)
        elem_dict = provider._element_to_dict(mock_elem)
        assert elem_dict is not None
        assert len(elem_dict["name"]) == 80
        assert elem_dict["name"].endswith("...")
