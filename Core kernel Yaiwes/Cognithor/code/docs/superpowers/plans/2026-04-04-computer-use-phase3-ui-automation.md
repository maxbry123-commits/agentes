# Computer Use Phase 3: Windows UI Automation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate Windows Accessibility Tree via pywinauto UIA to provide exact element coordinates, replacing vision-model coordinate estimation.

**Architecture:** New `UIAutomationProvider` reads interactive elements from the focused window via pywinauto UIA backend. `computer_screenshot()` tries UIA first; falls back to vision-only if UIA returns nothing. Vision always provides the textual description. Elements in prompts show their source (UIA vs vision).

**Tech Stack:** Python 3.13, pywinauto 0.6.9 (UIA backend), pytest

**Spec:** `docs/superpowers/specs/2026-04-04-computer-use-phase3-ui-automation-design.md`

---

## File Structure

| File | Responsibility |
|------|---------------|
| `src/jarvis/mcp/ui_automation.py` | **NEW** — UIAutomationProvider: reads OS-level elements |
| `src/jarvis/mcp/computer_use.py` | UIA-first element sourcing in computer_screenshot |
| `src/jarvis/core/cu_agent.py` | `_format_elements` source label |
| `src/jarvis/gateway/phases/tools.py` | Create UIAutomationProvider, pass to ComputerUseTools |
| `tests/test_mcp/test_ui_automation.py` | **NEW** — UIAutomationProvider tests |
| `tests/unit/test_computer_use_vision.py` | UIA integration in computer_screenshot |

---

### Task 1: UIAutomationProvider — Core Module

**Files:**
- Create: `src/jarvis/mcp/ui_automation.py`
- Create: `tests/test_mcp/test_ui_automation.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_mcp/test_ui_automation.py`:

```python
"""Tests for UIAutomationProvider — Windows Accessibility Tree integration."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestUIAutomationProvider:
    def test_import_and_instantiate(self):
        """Provider can be created even without pywinauto (graceful degradation)."""
        from jarvis.mcp.ui_automation import UIAutomationProvider

        provider = UIAutomationProvider()
        assert provider is not None

    def test_element_format_has_required_keys(self):
        """Each element dict must have name, type, x, y, clickable, source."""
        from jarvis.mcp.ui_automation import UIAutomationProvider

        provider = UIAutomationProvider()
        # Mock a pywinauto element
        mock_elem = MagicMock()
        mock_elem.window_text.return_value = "OK"
        mock_elem.element_info.control_type = "Button"
        mock_elem.element_info.visible = True
        mock_elem.is_enabled.return_value = True
        mock_elem.rectangle.return_value = MagicMock(
            left=100, top=200, right=200, bottom=230
        )

        elem_dict = provider._element_to_dict(mock_elem)
        assert elem_dict is not None
        assert elem_dict["name"] == "OK"
        assert elem_dict["type"] == "Button"
        assert elem_dict["x"] == 150  # center of 100-200
        assert elem_dict["y"] == 215  # center of 200-230
        assert elem_dict["w"] == 100
        assert elem_dict["h"] == 30
        assert elem_dict["clickable"] is True
        assert elem_dict["source"] == "uia"

    def test_excluded_control_types_filtered(self):
        """Container types like Pane, Group, etc. are excluded."""
        from jarvis.mcp.ui_automation import UIAutomationProvider

        provider = UIAutomationProvider()
        assert not provider._is_interactive_type("Pane")
        assert not provider._is_interactive_type("Group")
        assert not provider._is_interactive_type("ScrollViewer")
        assert not provider._is_interactive_type("Text")
        assert not provider._is_interactive_type("Image")
        assert not provider._is_interactive_type("Separator")

    def test_included_control_types_pass(self):
        """Interactive types like Button, Edit, etc. are included."""
        from jarvis.mcp.ui_automation import UIAutomationProvider

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
        """Output is capped at 30 elements."""
        from jarvis.mcp.ui_automation import UIAutomationProvider

        provider = UIAutomationProvider()
        # Create 50 mock elements
        elements = []
        for i in range(50):
            e = {
                "name": f"btn{i}", "type": "Button",
                "x": i * 10, "y": 100, "w": 50, "h": 20,
                "clickable": True, "text": "", "source": "uia",
            }
            elements.append(e)

        capped = provider._cap_and_sort(elements)
        assert len(capped) <= 30

    def test_sorting_top_left_to_bottom_right(self):
        """Elements sorted by approximate row (y//50) then x."""
        from jarvis.mcp.ui_automation import UIAutomationProvider

        provider = UIAutomationProvider()
        elements = [
            {"name": "C", "x": 500, "y": 100, "type": "Button",
             "w": 50, "h": 20, "clickable": True, "text": "", "source": "uia"},
            {"name": "A", "x": 100, "y": 100, "type": "Button",
             "w": 50, "h": 20, "clickable": True, "text": "", "source": "uia"},
            {"name": "B", "x": 200, "y": 300, "type": "Button",
             "w": 50, "h": 20, "clickable": True, "text": "", "source": "uia"},
        ]
        sorted_elems = provider._cap_and_sort(elements)
        assert sorted_elems[0]["name"] == "A"  # y=100, x=100
        assert sorted_elems[1]["name"] == "C"  # y=100, x=500
        assert sorted_elems[2]["name"] == "B"  # y=300

    def test_graceful_degradation_no_pywinauto(self):
        """If pywinauto is not available, get_focused_window_elements returns []."""
        from jarvis.mcp.ui_automation import UIAutomationProvider

        provider = UIAutomationProvider()
        with patch.object(provider, "_pywinauto_available", False):
            result = provider.get_focused_window_elements()
            assert result == []

    def test_graceful_degradation_exception(self):
        """If UIA access fails, returns [] instead of raising."""
        from jarvis.mcp.ui_automation import UIAutomationProvider

        provider = UIAutomationProvider()
        with patch.object(provider, "_get_foreground_window", side_effect=RuntimeError("COM error")):
            result = provider.get_focused_window_elements()
            assert result == []

    def test_zero_size_elements_excluded(self):
        """Elements with zero width or height are filtered out."""
        from jarvis.mcp.ui_automation import UIAutomationProvider

        provider = UIAutomationProvider()
        mock_elem = MagicMock()
        mock_elem.window_text.return_value = "Hidden"
        mock_elem.element_info.control_type = "Button"
        mock_elem.element_info.visible = True
        mock_elem.is_enabled.return_value = True
        mock_elem.rectangle.return_value = MagicMock(
            left=100, top=200, right=100, bottom=200  # zero size
        )

        elem_dict = provider._element_to_dict(mock_elem)
        assert elem_dict is None  # filtered out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_mcp/test_ui_automation.py -v`
Expected: ImportError — `ui_automation` module doesn't exist yet

- [ ] **Step 3: Implement UIAutomationProvider**

Create `src/jarvis/mcp/ui_automation.py`:

```python
"""Windows UI Automation provider — reads elements from the Accessibility Tree.

Uses pywinauto with UIA backend to enumerate interactive UI elements
of the foreground window. Provides exact coordinates, names, types,
and states directly from the OS.

Graceful degradation: if pywinauto is not installed or UIA access fails,
all methods return empty lists.
"""

from __future__ import annotations

import sys
from typing import Any

from jarvis.utils.logging import get_logger

log = get_logger(__name__)

_pywinauto_available = False
if sys.platform == "win32":
    try:
        from pywinauto import Desktop  # noqa: F401

        _pywinauto_available = True
    except ImportError:
        pass

_INTERACTIVE_TYPES = frozenset(
    {
        "Button",
        "Edit",
        "MenuItem",
        "ListItem",
        "TabItem",
        "Hyperlink",
        "CheckBox",
        "ComboBox",
        "RadioButton",
        "TreeItem",
        "Slider",
        "ToggleButton",
    }
)

_MAX_ELEMENTS = 30
_MAX_DEPTH = 8


class UIAutomationProvider:
    """Reads UI elements from the Windows Accessibility Tree via pywinauto UIA."""

    def __init__(self) -> None:
        self._pywinauto_available = _pywinauto_available

    @staticmethod
    def _is_interactive_type(control_type: str) -> bool:
        """Check if a control type is interactive (clickable/typeable)."""
        return control_type in _INTERACTIVE_TYPES

    def _element_to_dict(self, elem: Any) -> dict[str, Any] | None:
        """Convert a pywinauto element to a dict with standard format.

        Returns None if element should be filtered out.
        """
        try:
            control_type = elem.element_info.control_type
            if not self._is_interactive_type(control_type):
                return None

            rect = elem.rectangle()
            w = rect.right - rect.left
            h = rect.bottom - rect.top
            if w <= 0 or h <= 0:
                return None

            name = elem.window_text() or ""
            if len(name) > 80:
                name = name[:77] + "..."

            # Try to get value (for Edit fields, etc.)
            text = ""
            try:
                iface = elem.iface_value
                if iface:
                    text = str(iface.CurrentValue or "")
                    if len(text) > 100:
                        text = text[:97] + "..."
            except Exception:
                pass

            return {
                "name": name,
                "type": control_type,
                "x": rect.left + w // 2,
                "y": rect.top + h // 2,
                "w": w,
                "h": h,
                "clickable": bool(elem.is_enabled()),
                "text": text,
                "source": "uia",
            }
        except Exception:
            return None

    def _cap_and_sort(self, elements: list[dict]) -> list[dict]:
        """Sort by screen position (top-to-bottom, left-to-right) and cap."""
        elements.sort(key=lambda e: (e.get("y", 0) // 50, e.get("x", 0)))
        return elements[:_MAX_ELEMENTS]

    def _get_foreground_window(self) -> Any:
        """Get the foreground window wrapper via pywinauto."""
        from pywinauto import Desktop

        desktop = Desktop(backend="uia")
        windows = desktop.windows()
        if not windows:
            return None
        # First window in list is usually the foreground window
        # But we should find the actual foreground window
        try:
            import ctypes

            hwnd = ctypes.windll.user32.GetForegroundWindow()
            for w in windows:
                try:
                    if w.handle == hwnd:
                        return w
                except Exception:
                    continue
        except Exception:
            pass
        # Fallback: first window
        return windows[0] if windows else None

    def _walk_children(
        self, element: Any, depth: int, results: list[dict]
    ) -> None:
        """Recursively walk child elements up to max depth."""
        if depth > _MAX_DEPTH or len(results) >= _MAX_ELEMENTS * 2:
            return

        try:
            children = element.children()
        except Exception:
            return

        for child in children:
            elem_dict = self._element_to_dict(child)
            if elem_dict is not None:
                results.append(elem_dict)

            # Recurse into children (even non-interactive containers)
            self._walk_children(child, depth + 1, results)

    def get_focused_window_elements(self) -> list[dict]:
        """Return interactive elements of the foreground window.

        Returns list of dicts with: name, type, x, y, w, h, clickable, text, source.
        Returns empty list on any failure (graceful degradation).
        """
        if not self._pywinauto_available:
            return []

        try:
            window = self._get_foreground_window()
            if window is None:
                return []

            results: list[dict] = []
            self._walk_children(window, depth=0, results=results)

            return self._cap_and_sort(results)

        except Exception as exc:
            log.debug("uia_enumeration_failed", error=str(exc)[:200])
            return []
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_mcp/test_ui_automation.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/mcp/ui_automation.py tests/test_mcp/test_ui_automation.py
git commit -m "feat(cu): add UIAutomationProvider for Windows Accessibility Tree"
```

---

### Task 2: Integrate UIA into computer_screenshot

**Files:**
- Modify: `src/jarvis/mcp/computer_use.py:76-163`
- Test: `tests/unit/test_computer_use_vision.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/unit/test_computer_use_vision.py`:

```python
class TestUIAIntegration:
    @pytest.mark.asyncio
    async def test_uia_elements_replace_vision_elements(self):
        """When UIA returns elements, they replace vision elements."""
        mock_uia = MagicMock()
        mock_uia.get_focused_window_elements.return_value = [
            {"name": "OK", "type": "Button", "x": 150, "y": 200,
             "w": 80, "h": 30, "clickable": True, "text": "", "source": "uia"},
        ]

        mock_vision = MagicMock()
        mock_vision_result = MagicMock()
        mock_vision_result.success = True
        mock_vision_result.description = "Dialog with OK button"
        mock_vision_result.elements = [
            {"name": "OK", "type": "button", "x": 145, "y": 195}  # less accurate
        ]
        mock_vision.analyze_desktop = AsyncMock(return_value=mock_vision_result)

        tools = ComputerUseTools(vision_analyzer=mock_vision, uia_provider=mock_uia)

        with patch("jarvis.mcp.computer_use._take_screenshot_b64") as mock_ss:
            mock_ss.return_value = ("b64data", 1920, 1080, 1.0)
            result = await tools.computer_screenshot()

        assert result["success"] is True
        assert len(result["elements"]) == 1
        assert result["elements"][0]["source"] == "uia"
        assert result["elements"][0]["x"] == 150  # exact UIA coords
        assert "Dialog" in result["description"]  # vision still provides description

    @pytest.mark.asyncio
    async def test_vision_fallback_when_uia_empty(self):
        """When UIA returns no elements, vision elements are used."""
        mock_uia = MagicMock()
        mock_uia.get_focused_window_elements.return_value = []

        mock_vision = MagicMock()
        mock_vision_result = MagicMock()
        mock_vision_result.success = True
        mock_vision_result.description = "Game screen"
        mock_vision_result.elements = [
            {"name": "Play", "type": "button", "x": 500, "y": 300}
        ]
        mock_vision.analyze_desktop = AsyncMock(return_value=mock_vision_result)

        tools = ComputerUseTools(vision_analyzer=mock_vision, uia_provider=mock_uia)

        with patch("jarvis.mcp.computer_use._take_screenshot_b64") as mock_ss:
            mock_ss.return_value = ("b64data", 1920, 1080, 1.0)
            result = await tools.computer_screenshot()

        assert result["elements"][0]["name"] == "Play"  # from vision
        assert "Game screen" in result["description"]

    @pytest.mark.asyncio
    async def test_no_uia_provider_uses_vision_only(self):
        """When no UIA provider is set, works exactly as before."""
        mock_vision = MagicMock()
        mock_vision_result = MagicMock()
        mock_vision_result.success = True
        mock_vision_result.description = "Desktop"
        mock_vision_result.elements = [{"name": "Start", "type": "button", "x": 50, "y": 1060}]
        mock_vision.analyze_desktop = AsyncMock(return_value=mock_vision_result)

        tools = ComputerUseTools(vision_analyzer=mock_vision)  # no uia_provider

        with patch("jarvis.mcp.computer_use._take_screenshot_b64") as mock_ss:
            mock_ss.return_value = ("b64data", 1920, 1080, 1.0)
            result = await tools.computer_screenshot()

        assert result["elements"][0]["name"] == "Start"

    @pytest.mark.asyncio
    async def test_uia_exception_falls_back_to_vision(self):
        """If UIA throws, fall back to vision."""
        mock_uia = MagicMock()
        mock_uia.get_focused_window_elements.side_effect = RuntimeError("COM error")

        mock_vision = MagicMock()
        mock_vision_result = MagicMock()
        mock_vision_result.success = True
        mock_vision_result.description = "Screen"
        mock_vision_result.elements = [{"name": "X", "type": "button", "x": 10, "y": 10}]
        mock_vision.analyze_desktop = AsyncMock(return_value=mock_vision_result)

        tools = ComputerUseTools(vision_analyzer=mock_vision, uia_provider=mock_uia)

        with patch("jarvis.mcp.computer_use._take_screenshot_b64") as mock_ss:
            mock_ss.return_value = ("b64data", 1920, 1080, 1.0)
            result = await tools.computer_screenshot()

        assert result["elements"][0]["name"] == "X"  # vision fallback
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_computer_use_vision.py::TestUIAIntegration -v`
Expected: TypeError — `ComputerUseTools.__init__` doesn't accept `uia_provider` yet

- [ ] **Step 3: Add `uia_provider` to ComputerUseTools**

In `src/jarvis/mcp/computer_use.py`, update `__init__`:

```python
    def __init__(self, vision_analyzer: Any = None, uia_provider: Any = None) -> None:
        self._vision = vision_analyzer
        self._uia_provider = uia_provider
        self._last_scale_factor: float = 1.0
```

- [ ] **Step 4: Replace element sourcing in `computer_screenshot`**

Replace the element/description block in `computer_screenshot` (lines 128-153):

```python
            self._last_scale_factor = scale_factor

            # Try UIA first for exact element coordinates
            uia_elements: list[dict] = []
            if self._uia_provider:
                try:
                    uia_elements = await loop.run_in_executor(
                        None, self._uia_provider.get_focused_window_elements
                    )
                except Exception:
                    pass

            if uia_elements:
                elements = uia_elements
                # Vision still provides description (scene context)
                if self._vision:
                    try:
                        result = await self._vision.analyze_desktop(
                            b64, task_context=task_context
                        )
                        description = (
                            result.description
                            if result.success
                            else f"Screenshot taken ({width}x{height})."
                        )
                    except Exception as exc:
                        description = f"Screenshot taken ({width}x{height}). Vision error: {exc}"
                else:
                    description = f"Screenshot taken ({width}x{height})."
                log.info(
                    "desktop_uia_elements",
                    count=len(elements),
                    names=[e["name"] for e in elements[:5]],
                )
            elif self._vision:
                # Fallback: vision provides both description AND elements
                try:
                    result = await self._vision.analyze_desktop(
                        b64, task_context=task_context
                    )
                    description = (
                        result.description
                        if result.success
                        else (
                            f"Screenshot taken ({width}x{height}). "
                            f"Vision analysis failed: {result.error}"
                        )
                    )
                    elements = result.elements
                    if elements:
                        log.info(
                            "desktop_vision_elements",
                            count=len(elements),
                            names=[e["name"] for e in elements[:5]],
                        )
                except Exception as exc:
                    description = f"Screenshot taken ({width}x{height}). Vision error: {exc}"
                    elements = []
            else:
                description = (
                    f"Screenshot taken ({width}x{height}). "
                    "No vision analyzer or UIA — use coordinates from previous analysis."
                )
                elements = []
```

- [ ] **Step 5: Update `register_computer_use_tools` signature**

Add `uia_provider` parameter:

```python
def register_computer_use_tools(
    client: Any,
    vision_analyzer: Any = None,
    uia_provider: Any = None,
) -> ComputerUseTools | None:
```

And pass it to the constructor:

```python
    tools = ComputerUseTools(vision_analyzer=vision_analyzer, uia_provider=uia_provider)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/unit/test_computer_use_vision.py -v`
Expected: All PASS (existing + new)

- [ ] **Step 7: Commit**

```bash
git add src/jarvis/mcp/computer_use.py tests/unit/test_computer_use_vision.py
git commit -m "feat(cu): UIA-first element sourcing in computer_screenshot with vision fallback"
```

---

### Task 3: Source Label in `_format_elements`

**Files:**
- Modify: `src/jarvis/core/cu_agent.py:381-389`
- Test: `tests/test_core/test_cu_agent.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_core/test_cu_agent.py`:

```python
class TestFormatElementsSourceLabel:
    def _make_agent(self):
        planner = MagicMock()
        planner._ollama = AsyncMock()
        mcp = MagicMock()
        mcp._builtin_handlers = {}
        return CUAgentExecutor(planner, mcp, MagicMock(), MagicMock(), {})

    def test_uia_source_label(self):
        agent = self._make_agent()
        elements = [
            {"name": "OK", "type": "Button", "x": 100, "y": 200, "text": "", "source": "uia"},
        ]
        result = agent._format_elements(elements)
        assert "exakte Koordinaten" in result
        assert "OK" in result

    def test_vision_source_label(self):
        agent = self._make_agent()
        elements = [
            {"name": "OK", "type": "Button", "x": 100, "y": 200, "text": ""},
        ]
        result = agent._format_elements(elements)
        assert "geschaetzte Koordinaten" in result

    def test_empty_elements(self):
        agent = self._make_agent()
        result = agent._format_elements([])
        assert "keine Elemente" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_core/test_cu_agent.py::TestFormatElementsSourceLabel -v`
Expected: FAIL — no source label in current output

- [ ] **Step 3: Update `_format_elements`**

Replace in `src/jarvis/core/cu_agent.py`:

```python
    @staticmethod
    def _format_elements(elements: list[dict]) -> str:
        """Format elements list for the decide prompt with source label."""
        if not elements:
            return "(keine Elemente erkannt)"
        source = elements[0].get("source", "vision")
        source_label = (
            "Windows UI Automation — exakte Koordinaten"
            if source == "uia"
            else "Vision-Analyse — geschaetzte Koordinaten"
        )
        compact = [
            {k: e[k] for k in ("name", "type", "x", "y", "text") if k in e}
            for e in elements[:15]
        ]
        return (
            f"(Quelle: {source_label})\n"
            + json.dumps(compact, ensure_ascii=False, indent=None)
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_core/test_cu_agent.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/core/cu_agent.py tests/test_core/test_cu_agent.py
git commit -m "feat(cu): _format_elements shows UIA/vision source label"
```

---

### Task 4: Gateway Wiring — UIAutomationProvider

**Files:**
- Modify: `src/jarvis/gateway/phases/tools.py:484-496`

- [ ] **Step 1: Update tools.py to create and wire UIA provider**

In `src/jarvis/gateway/phases/tools.py`, replace the CU block (lines 484-496):

```python
    # Computer Use (screenshot + coordinate clicking) — guarded by config.tools.computer_use_enabled
    if getattr(getattr(config, "tools", None), "computer_use_enabled", False):
        try:
            from jarvis.mcp.computer_use import register_computer_use_tools

            vision = getattr(gateway, "_vision_analyzer", None) if gateway else None

            # Create UIA provider for exact element coordinates (Windows only)
            uia_provider = None
            import sys as _sys

            if _sys.platform == "win32":
                try:
                    from jarvis.mcp.ui_automation import UIAutomationProvider

                    uia_provider = UIAutomationProvider()
                    log.info("ui_automation_provider_created")
                except Exception:
                    log.debug("ui_automation_not_available", exc_info=True)

            cu_tools = register_computer_use_tools(
                mcp_client, vision_analyzer=vision, uia_provider=uia_provider
            )
            if cu_tools:
                if gateway:
                    gateway._cu_tools = cu_tools
                log.info("computer_use_tools_registered")
        except Exception:
            log.debug("computer_use_not_registered", exc_info=True)
    else:
        log.info("computer_use_disabled_by_config")
```

- [ ] **Step 2: Run gateway tests**

Run: `pytest tests/test_integration/test_phase10_13_wiring.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/jarvis/gateway/phases/tools.py
git commit -m "feat(cu): create UIAutomationProvider and wire into ComputerUseTools"
```

---

### Task 5: Add pywinauto to pyproject.toml Dependencies

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Check current desktop extras**

Find the `[desktop]` extras section in `pyproject.toml` and add `pywinauto>=0.6.8`.

```toml
[project.optional-dependencies]
desktop = [
    "pyautogui>=0.9",
    "mss>=9.0",
    "Pillow>=10.0",
    "pyperclip>=1.8",
    "pywinauto>=0.6.8",
]
```

- [ ] **Step 2: Commit**

```bash
git add pyproject.toml
git commit -m "feat(cu): add pywinauto to [desktop] optional dependencies"
```

---

### Task 6: Final Verification

**Files:** None (verification only)

- [ ] **Step 1: Run all CU-related tests**

Run: `pytest tests/test_core/test_cu_agent.py tests/unit/test_computer_use_vision.py tests/test_browser/test_vision.py tests/test_mcp/test_ui_automation.py -v`
Expected: All PASS

- [ ] **Step 2: Run gateway tests**

Run: `pytest tests/test_integration/test_phase10_13_wiring.py -v`
Expected: PASS

- [ ] **Step 3: Run broad test sweep**

Run: `pytest tests/ -x -q --ignore=tests/test_skills/test_marketplace_persistence.py --ignore=tests/test_mcp/test_tool_registry_db.py`
Expected: No new failures

- [ ] **Step 4: Verify ruff lint**

Run: `ruff format --check src/ tests/ && ruff check src/jarvis/mcp/ui_automation.py src/jarvis/mcp/computer_use.py src/jarvis/core/cu_agent.py`
Expected: Clean

- [ ] **Step 5: Live smoke test (manual)**

Run in Python REPL:
```python
from jarvis.mcp.ui_automation import UIAutomationProvider
p = UIAutomationProvider()
elements = p.get_focused_window_elements()
for e in elements[:10]:
    print(f"{e['name'][:30]:30s} {e['type']:15s} ({e['x']}, {e['y']})")
```

Verify: Elements are printed with sensible names, types, and coordinates.

- [ ] **Step 6: Final commit**

```bash
git commit --allow-empty -m "feat(cu): Phase 3 Windows UI Automation complete — exact element coordinates from OS Accessibility Tree"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] Section 1 (UIAutomationProvider): Task 1
- [x] Section 2 (Integration in computer_screenshot): Task 2
- [x] Section 3 (Source label in prompts): Task 3
- [x] Section 4 (Gateway wiring): Task 4
- [x] Section 5 (Files changed): Tasks 1-4 cover all files
- [x] Section 6 (Degradation guarantees): Tests in Task 1 (no pywinauto, exception, zero-size)
- [x] Section 7 (Dependencies): Task 5

**Placeholder scan:** No TBD, TODO, or vague instructions.

**Type consistency:**
- `UIAutomationProvider` created in Task 1, used in Task 2 (computer_use.py) and Task 4 (tools.py) ✓
- `uia_provider: Any | None` in `ComputerUseTools.__init__` and `register_computer_use_tools` ✓
- `_element_to_dict` returns `dict | None`, `get_focused_window_elements` returns `list[dict]` ✓
- `_is_interactive_type`, `_cap_and_sort` helper methods used in tests and implementation ✓
- Element format `{name, type, x, y, w, h, clickable, text, source}` consistent across all files ✓
