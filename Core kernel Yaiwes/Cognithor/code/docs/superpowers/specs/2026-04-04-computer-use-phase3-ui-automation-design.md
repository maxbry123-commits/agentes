# Computer Use Phase 3: Windows UI Automation — Design Spec

**Date:** 2026-04-04
**Status:** Approved
**Depends on:** Phase 2A-2E (all complete)

## Goal

Integrate Windows Accessibility Tree via pywinauto UIA backend to provide exact element coordinates, names, types, and states directly from the OS. This replaces the vision model's approximate pixel coordinate estimation for element detection while keeping vision for scene description.

## Architecture

**Separation of concerns:**
- `ui_automation.py` (NEW) — reads OS-level element data via pywinauto UIA
- `computer_use.py` — takes screenshots, executes actions via pyautogui (unchanged action model)
- `vision.py` — provides textual scene description (no longer provides elements when UIA is available)

**Data flow:**
```
computer_screenshot()
  ├── _take_screenshot_b64() → base64 image
  ├── UIAutomationProvider.get_focused_window_elements() → elements with exact coords
  │   └── (if empty) VisionAnalyzer.analyze_desktop() → elements with estimated coords
  ├── VisionAnalyzer.analyze_desktop() → textual description (always, for context)
  └── return {description, elements, width, height}
```

UIA elements have priority. Vision elements are fallback only when UIA returns nothing.

## 1. UIAutomationProvider

New file: `src/jarvis/mcp/ui_automation.py`

### Class

```python
class UIAutomationProvider:
    """Reads UI elements from the Windows Accessibility Tree via pywinauto UIA."""

    def get_focused_window_elements(self) -> list[dict]:
        """Returns interactive elements of the foreground window.

        Returns list of dicts, each with:
          name, type, x, y, w, h, clickable, text, source
        where x,y is the center of the BoundingRect.
        """
```

### Element Format

Compatible with the existing vision element format:

```python
{
    "name": "Suchen",           # element.window_text()
    "type": "Edit",             # control_type
    "x": 450,                   # BoundingRect center x
    "y": 320,                   # BoundingRect center y
    "w": 200,                   # width
    "h": 30,                    # height
    "clickable": True,          # IsEnabled
    "text": "Suchbegriff...",   # value pattern current_value if available
    "source": "uia",            # distinguishes from vision elements
}
```

### Filtering Rules

Only interactive, visible elements:

**Included control types:** Button, Edit, MenuItem, ListItem, TabItem, Hyperlink, CheckBox, ComboBox, RadioButton, TreeItem, Slider, ToggleButton

**Excluded:** Pane, Group, ScrollViewer, Window, Document, Text, Image, Separator, StatusBar, ToolBar, Header, HeaderItem, ScrollBar, Thumb

**Visibility filters:**
- `IsOffscreen == False`
- `IsEnabled == True`
- BoundingRect has non-zero width and height

**Limits:**
- Max traversal depth: 8 (prevents infinite recursion in deep trees)
- Max elements: 30 (sorted by screen position: top-left to bottom-right)

### Sorting

Elements sorted by `(y // 50, x)` — groups elements into approximate rows (50px buckets), then sorts left-to-right within each row. This gives the LLM a natural reading-order.

### Graceful Degradation

```python
try:
    from pywinauto import Desktop
except ImportError:
    # pywinauto not installed — provider returns empty list
```

Any exception during UIA access (AccessDenied, no focus window, COM error) returns empty list. No exception propagates to caller.

## 2. Integration in computer_screenshot

`ComputerUseTools` gains `_uia_provider: UIAutomationProvider | None` in constructor.

In `computer_screenshot()`:

```python
# Try UIA first for exact element coordinates
uia_elements = []
if self._uia_provider:
    try:
        loop = asyncio.get_running_loop()
        uia_elements = await loop.run_in_executor(
            None, self._uia_provider.get_focused_window_elements
        )
    except Exception:
        pass

if uia_elements:
    elements = uia_elements
    # Vision still runs for description only (no element parsing)
    if self._vision:
        result = await self._vision.analyze_desktop(b64, task_context=task_context)
        description = result.description if result.success else f"Screenshot ({width}x{height})"
elif self._vision:
    # Fallback: vision provides both description AND elements
    result = await self._vision.analyze_desktop(b64, task_context=task_context)
    description = result.description if result.success else f"Screenshot ({width}x{height})"
    elements = result.elements
else:
    description = f"Screenshot ({width}x{height}). No vision or UIA available."
```

UIA runs in executor (blocking pywinauto call, ~100-300ms).

## 3. Element Source in Prompts

`_format_elements()` in `CUAgentExecutor` adds source hint:

```python
@staticmethod
def _format_elements(elements: list[dict]) -> str:
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
    return f"(Quelle: {source_label})\n" + json.dumps(compact, ensure_ascii=False, indent=None)
```

## 4. Gateway Wiring

In `src/jarvis/gateway/phases/tools.py`, when creating `ComputerUseTools`:

```python
# Create UIA provider if on Windows
uia_provider = None
if sys.platform == "win32":
    try:
        from jarvis.mcp.ui_automation import UIAutomationProvider
        uia_provider = UIAutomationProvider()
    except Exception:
        pass

cu_tools = register_computer_use_tools(
    mcp_client, vision_analyzer=vision, uia_provider=uia_provider
)
```

`register_computer_use_tools` and `ComputerUseTools.__init__` gain an `uia_provider` parameter.

## 5. Files Changed

| File | Change |
|------|--------|
| `src/jarvis/mcp/ui_automation.py` | **NEW** — UIAutomationProvider class |
| `src/jarvis/mcp/computer_use.py` | `_uia_provider` param, UIA-first element sourcing in computer_screenshot |
| `src/jarvis/core/cu_agent.py` | `_format_elements()` shows source label |
| `src/jarvis/gateway/phases/tools.py` | Create UIAutomationProvider, pass to ComputerUseTools |
| `tests/test_mcp/test_ui_automation.py` | **NEW** — UIAutomationProvider tests |
| `tests/unit/test_computer_use_vision.py` | UIA integration tests in computer_screenshot |

### Unchanged

- `browser/vision.py` — no changes (still provides descriptions)
- `core/planner.py` — no changes
- `core/gatekeeper.py` — no changes

## 6. Degradation Guarantees

- pywinauto not installed → empty UIA list → vision fallback (existing behavior)
- UIA access fails → empty list → vision fallback
- App without UIA support (games, custom renderers) → few/no UIA elements → vision fallback
- Non-Windows platform → UIAutomationProvider not created → vision only
- All existing tests remain compatible (UIA provider defaults to None)

## 7. Dependencies

- `pywinauto>=0.6.8` — already installed (v0.6.9). Added to `[desktop]` extras in pyproject.toml.
- No new dependencies needed.
