# Computer Use Phase 2A: Vision Engine — Design Spec

**Date**: 2026-04-02
**Status**: Approved
**Scope**: Desktop Vision integration for Computer Use tools
**Depends on**: Phase 1 Computer Use (complete in v0.70.0)
**Roadmap**: `docs/superpowers/specs/2026-04-02-computer-use-phase2-roadmap.md`

## Problem

The vision model `qwen3-vl:32b` is configured and loaded (`vision_analyzer_created model=qwen3-vl:32b` in logs) but `computer_screenshot` never calls it. The code in `computer_use.py` checks for `analyze_image_b64()` which does not exist on `VisionAnalyzer`. The actual methods are `analyze_screenshot()`, `find_element_by_vision()`, and `describe_page()`. As a result, screenshots return fallback text: "Screenshot taken (WxH). Vision analyzer not available for element detection."

Additionally, the existing `VisionAnalyzer` is browser-focused (HTML context, CSS selectors). Desktop screenshots need pixel coordinates, window identification, and UI element detection without HTML context.

## Solution

Add a `analyze_desktop()` method to `VisionAnalyzer` with a desktop-specific prompt that asks for structured JSON with pixel coordinates. Wire it into `computer_screenshot`. Replace PowerShell-based window focusing with vision-based screenshot→click focusing. Update planner prompt with the new iterative flow.

## Data Flow

```
User: "Oeffne den Taschenrechner und tippe 1+4="

1. Planner: exec_command("start calc.exe")
   → Executor runs command
   → 2s wait
   → Auto: computer_screenshot() → analyze_desktop()
   → Vision sees: [{"name":"Rechner","type":"window","x":200,"y":300,...}]
   → Auto: computer_click(x=200, y=300) → Rechner gets focus

2. Planner: computer_screenshot()
   → Vision: [{"name":"Eingabefeld","type":"textfield","x":200,"y":400,...}]
   → Planner sees elements with coordinates

3. Planner: computer_click(x=200, y=400)
   → Clicks on the calculator input area

4. Planner: computer_type(text="1+4=")
   → Clipboard paste into focused calculator

5. Verification: computer_screenshot()
   → Vision sees: "459" displayed in calculator
   → Response: "Erledigt. Der Taschenrechner zeigt 459."
```

## Component Changes

### 1. `src/jarvis/browser/vision.py` — New `analyze_desktop()` Method

#### 1.1 Desktop-Specific Prompt

Add as module-level constant after existing prompts (after line 76):

```python
_DESKTOP_ANALYSIS_PROMPT = (
    "Analysiere diesen Desktop-Screenshot. Identifiziere ALLE sichtbaren "
    "UI-Elemente.\n\n"
    "Fuer JEDES Element liefere:\n"
    "- name: Beschreibender Name (z.B. 'Adressleiste', 'Suchfeld', 'Rechner')\n"
    "- type: window | button | textfield | menu | icon | tab | scrollbar | link | other\n"
    "- x: X-Pixel-Koordinate der Mitte des Elements\n"
    "- y: Y-Pixel-Koordinate der Mitte des Elements\n"
    "- w: Breite in Pixeln (geschaetzt)\n"
    "- h: Hoehe in Pixeln (geschaetzt)\n"
    "- text: Sichtbarer Text im Element (falls vorhanden)\n"
    "- clickable: true/false\n\n"
    "Antworte NUR mit validem JSON:\n"
    '{"elements": [{"name": "...", "type": "...", "x": 0, "y": 0, '
    '"w": 0, "h": 0, "text": "...", "clickable": true}]}'
)

_DESKTOP_CONTEXTUAL_PROMPT_SUFFIX = (
    "\n\nKontext: {context}\n"
    "Fokussiere auf Elemente die fuer diese Aufgabe relevant sind."
)
```

#### 1.2 New Method Signature

Add after `describe_page()` (after line 170):

```python
async def analyze_desktop(
    self,
    screenshot_b64: str,
    prompt: str = "",
    task_context: str = "",
) -> VisionAnalysisResult:
    """Analyze a desktop screenshot and identify UI elements with coordinates.

    Unlike analyze_screenshot (browser-focused), this method is optimized
    for desktop environments: pixel coordinates instead of CSS selectors,
    window detection, taskbar elements, etc.

    Args:
        screenshot_b64: Base64-encoded screenshot (PNG).
        prompt: Optional custom prompt (default: desktop element detection).
        task_context: Optional task description to focus the analysis
            (e.g., "User will Reddit oeffnen").

    Returns:
        VisionAnalysisResult with description and elements list.
        Each element dict: {name, type, x, y, w, h, text, clickable}.
    """
    if not self.is_enabled:
        return VisionAnalysisResult(error="Vision nicht aktiviert")

    if not screenshot_b64:
        return VisionAnalysisResult(error="Kein Screenshot-Daten")

    # Build prompt
    effective_prompt = prompt or _DESKTOP_ANALYSIS_PROMPT
    if task_context and not prompt:
        effective_prompt += _DESKTOP_CONTEXTUAL_PROMPT_SUFFIX.format(
            context=task_context
        )

    # Send to vision LLM (same pipeline as browser analysis)
    result = await self._send_vision_request(screenshot_b64, effective_prompt)

    # Parse structured elements from response
    if result.success and result.description:
        result.elements = _parse_desktop_elements(result.description)

    return result
```

#### 1.3 JSON Element Parser

Add as module-level function after `_DESKTOP_CONTEXTUAL_PROMPT_SUFFIX`:

```python
def _parse_desktop_elements(raw_response: str) -> list[dict[str, Any]]:
    """Parse structured UI elements from vision model response.

    Uses the same 4-tier fallback strategy as the memory pipeline:
    1. Direct json.loads
    2. Extract ```json ... ``` markdown block
    3. Regex extraction of elements array
    4. Empty list fallback

    Returns:
        List of element dicts with name, type, x, y, w, h, text, clickable.
    """
    import json
    import re

    # Tier 1: direct parse
    try:
        data = json.loads(raw_response)
        if isinstance(data, dict) and "elements" in data:
            return _validate_elements(data["elements"])
    except (json.JSONDecodeError, ValueError):
        pass

    # Tier 2: markdown code block
    md_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw_response, re.DOTALL)
    if md_match:
        try:
            data = json.loads(md_match.group(1))
            if isinstance(data, dict) and "elements" in data:
                return _validate_elements(data["elements"])
        except (json.JSONDecodeError, ValueError):
            pass

    # Tier 3: find JSON object in response
    json_match = re.search(r"\{[\s\S]*\"elements\"[\s\S]*\}", raw_response)
    if json_match:
        try:
            data = json.loads(json_match.group())
            if isinstance(data, dict) and "elements" in data:
                return _validate_elements(data["elements"])
        except (json.JSONDecodeError, ValueError):
            pass

    # Tier 4: empty list (vision model didn't return structured data)
    return []


def _validate_elements(elements: Any) -> list[dict[str, Any]]:
    """Validate and normalize element dicts from vision model."""
    if not isinstance(elements, list):
        return []

    validated = []
    for el in elements:
        if not isinstance(el, dict):
            continue
        # Require at minimum name and coordinates
        if "name" not in el or "x" not in el or "y" not in el:
            continue
        validated.append({
            "name": str(el.get("name", "")),
            "type": str(el.get("type", "other")),
            "x": int(el.get("x", 0)),
            "y": int(el.get("y", 0)),
            "w": int(el.get("w", 0)),
            "h": int(el.get("h", 0)),
            "text": str(el.get("text", "")),
            "clickable": bool(el.get("clickable", False)),
        })

    return validated
```

### 2. `src/jarvis/mcp/computer_use.py` — Wire Vision Into Screenshot

#### 2.1 Replace the `computer_screenshot` Vision Call

Replace the entire `if self._vision:` block (lines 90-122) in `computer_screenshot()`:

**Current (broken):**
```python
if self._vision:
    try:
        if hasattr(self._vision, "analyze_image_b64"):
            description = await self._vision.analyze_image_b64(...)
        elif hasattr(self._vision, "analyze"):
            description = await self._vision.analyze(...)
        else:
            description = f"Screenshot taken ({width}x{height}). Vision analyzer not available..."
    except Exception as exc:
        description = f"Screenshot taken ({width}x{height}). Vision analysis failed: {exc}"
else:
    description = f"Screenshot taken ({width}x{height}). No vision analyzer..."
```

**New:**
```python
elements = []
if self._vision:
    try:
        result = await self._vision.analyze_desktop(b64)
        description = result.description if result.success else (
            f"Screenshot taken ({width}x{height}). Vision analysis failed: {result.error}"
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
else:
    description = (
        f"Screenshot taken ({width}x{height}). "
        "No vision analyzer — use coordinates from previous analysis."
    )
```

#### 2.2 Return Elements in Screenshot Result

Update the return dict to include elements:

```python
return {
    "success": True,
    "width": width,
    "height": height,
    "description": description,
    "elements": elements,
}
```

#### 2.3 Update Input Schema for `computer_screenshot`

Add `task_context` parameter to `computer_screenshot`:

```python
async def computer_screenshot(self, monitor: int = 0, task_context: str = "") -> dict[str, Any]:
```

And pass it through:
```python
result = await self._vision.analyze_desktop(b64, task_context=task_context)
```

Update the registration schema:
```python
input_schema={
    "type": "object",
    "properties": {
        "monitor": {
            "type": "integer",
            "description": "0=all monitors (default), 1=primary, 2+=specific monitor",
        },
        "task_context": {
            "type": "string",
            "description": "What the user wants to do (helps focus element detection)",
        },
    },
},
```

### 3. `src/jarvis/core/executor.py` — Vision-Based Window Focus

#### 3.1 Replace PowerShell Focus with Vision+Click

Replace the entire PowerShell block (lines 327-358) in `_run_with_sem`:

```python
# After launching a GUI app, wait then focus via vision
if action.tool == "exec_command" and result.success and _has_computer_use:
    await asyncio.sleep(2.0)
    # Vision-based focusing: screenshot → find window → click on it
    try:
        _ss_handler = self._mcp_client._builtin_handlers.get("computer_screenshot")
        _click_handler = self._mcp_client._builtin_handlers.get("computer_click")
        if _ss_handler and _click_handler:
            _ss = await _ss_handler()
            _elements = _ss.get("elements", [])
            # Find the most prominent window element
            _windows = [e for e in _elements
                        if e.get("type") == "window" and e.get("clickable", True)]
            if _windows:
                _target = _windows[0]
                await _click_handler(x=_target["x"], y=_target["y"])
                await asyncio.sleep(0.3)
                log.info(
                    "vision_focus_window",
                    name=_target.get("name", "?"),
                    x=_target["x"],
                    y=_target["y"],
                )
            else:
                log.debug("vision_focus_no_windows_found", elements=len(_elements))
    except Exception:
        log.debug("vision_focus_failed", exc_info=True)
```

**Fallback behavior:** If vision finds no windows or fails entirely, execution continues without focusing (same as before — best effort).

**No PowerShell dependency:** The entire `subprocess.run(["powershell", ...])` block is removed. Works on any OS.

### 4. `src/jarvis/core/planner.py` — Updated Prompt

#### 4.1 Updated CU Instructions

Replace the current COMPUTER USE block (lines 100-111):

```python
**COMPUTER USE (Desktop-Automation):** Du KANNST den Desktop des Nutzers \
steuern! Wenn der Nutzer dich bittet ein Programm zu oeffnen und darin zu \
tippen/klicken, nutze die computer_* Tools. Du hast: \
computer_screenshot (zeigt dir den Bildschirm mit UI-Elementen und Koordinaten), \
computer_click (klickt auf x,y Koordinaten aus dem Screenshot), \
computer_type (tippt Text via Clipboard-Paste), \
computer_hotkey (drueckt Tastenkombinationen wie Enter, Alt+Tab). \
ABLAUF: Schritt 1: exec_command zum Programm-Start. Schritt 2: \
computer_screenshot -- du erhaeltst eine Liste von UI-Elementen mit \
Pixel-Koordinaten (x, y). Schritt 3: computer_click mit den Koordinaten \
eines Elements aus dem Screenshot. Schritt 4: computer_type zum Tippen. \
WICHTIG: Nutze IMMER die Koordinaten aus dem Screenshot-Ergebnis fuer Clicks. \
Klicke IMMER auf ein Element BEVOR du computer_type verwendest. \
Jeder Schritt ist ein EIGENER Step im JSON-Plan. SAGE NIEMALS \
"ich kann keine GUI steuern" -- du KANNST es.
```

#### 4.2 Updated Few-Shot Example

Replace the calculator example (lines 139-150):

```python
Beispiel -- "Oeffne den Taschenrechner und tippe 1+4=":
```json
{{"goal": "Taschenrechner oeffnen und Rechnung eintippen", \
"reasoning": "Desktop-Automation: oeffnen, Screenshot fuer Koordinaten, klicken, tippen.", \
"steps": [\
{{"tool": "exec_command", "params": {{"command": "start calc.exe"}}, \
"rationale": "Taschenrechner starten"}}, \
{{"tool": "computer_screenshot", "params": {{}}, \
"rationale": "Bildschirm ansehen, UI-Elemente mit Koordinaten erhalten"}}, \
{{"tool": "computer_click", "params": {{"x": 0, "y": 0}}, \
"rationale": "Auf Taschenrechner klicken (Koordinaten aus Screenshot)"}}, \
{{"tool": "computer_type", "params": {{"text": "1+4="}}, \
"rationale": "Rechnung eintippen"}}], "confidence": 0.85}}
```
```

### 5. `src/jarvis/gateway/gateway.py` — Verification Screenshot Update

#### 5.1 Pass Elements Through in Verification

The existing verification screenshot (lines 3071-3097) already calls `computer_screenshot`. After the vision fix, it will automatically get elements. No code change needed — the tool result will now contain the description from the vision model instead of the fallback text.

The `_formulate_response()` will receive the vision description in `all_results`, enabling Cognithor to say "Der Taschenrechner zeigt 459" instead of "Screenshot taken (1920x1080)".

## Tests

### Test 1: `_parse_desktop_elements` — JSON Parsing

```python
class TestParseDesktopElements:
    def test_valid_json(self):
        raw = json.dumps({"elements": [
            {"name": "Rechner", "type": "window", "x": 200, "y": 300,
             "w": 400, "h": 500, "text": "459", "clickable": True}
        ]})
        elements = _parse_desktop_elements(raw)
        assert len(elements) == 1
        assert elements[0]["name"] == "Rechner"
        assert elements[0]["x"] == 200
        assert elements[0]["clickable"] is True

    def test_json_in_markdown_block(self):
        raw = "Hier ist meine Analyse:\n```json\n" + json.dumps({
            "elements": [{"name": "Button", "type": "button", "x": 50, "y": 60}]
        }) + "\n```"
        elements = _parse_desktop_elements(raw)
        assert len(elements) == 1
        assert elements[0]["name"] == "Button"

    def test_missing_coordinates_skipped(self):
        raw = json.dumps({"elements": [
            {"name": "OK", "type": "button"},  # no x, y
            {"name": "Cancel", "type": "button", "x": 100, "y": 200},
        ]})
        elements = _parse_desktop_elements(raw)
        assert len(elements) == 1
        assert elements[0]["name"] == "Cancel"

    def test_garbage_returns_empty(self):
        elements = _parse_desktop_elements("This is not JSON at all.")
        assert elements == []

    def test_think_tags_stripped(self):
        raw = "<think>Let me analyze...</think>\n" + json.dumps({
            "elements": [{"name": "Start", "type": "button", "x": 24, "y": 1060}]
        })
        elements = _parse_desktop_elements(raw)
        assert len(elements) == 1
```

### Test 2: `_validate_elements` — Type Safety

```python
class TestValidateElements:
    def test_int_coercion(self):
        elements = _validate_elements([
            {"name": "Test", "x": "100", "y": "200", "w": "50", "h": "30"}
        ])
        assert elements[0]["x"] == 100
        assert isinstance(elements[0]["x"], int)

    def test_non_list_returns_empty(self):
        assert _validate_elements("not a list") == []
        assert _validate_elements(None) == []

    def test_non_dict_entries_skipped(self):
        assert _validate_elements(["not a dict", 42]) == []

    def test_defaults_applied(self):
        elements = _validate_elements([{"name": "X", "x": 10, "y": 20}])
        assert elements[0]["type"] == "other"
        assert elements[0]["w"] == 0
        assert elements[0]["text"] == ""
        assert elements[0]["clickable"] is False
```

### Test 3: `VisionAnalyzer.analyze_desktop` — Integration

```python
class TestAnalyzeDesktop:
    def _make_analyzer(self, llm_response: str) -> tuple[VisionAnalyzer, AsyncMock]:
        llm = AsyncMock()
        llm.chat = AsyncMock(return_value={
            "message": {"role": "assistant", "content": llm_response},
        })
        cfg = VisionConfig(enabled=True, model="qwen3-vl:32b", backend_type="ollama")
        return VisionAnalyzer(llm, cfg), llm

    @pytest.mark.asyncio
    async def test_returns_elements(self):
        response = json.dumps({"elements": [
            {"name": "Rechner", "type": "window", "x": 200, "y": 300,
             "w": 400, "h": 500, "text": "", "clickable": True},
        ]})
        v, llm = self._make_analyzer(response)
        result = await v.analyze_desktop("base64data")

        assert result.success is True
        assert len(result.elements) == 1
        assert result.elements[0]["name"] == "Rechner"
        assert result.elements[0]["x"] == 200
        llm.chat.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_disabled_returns_error(self):
        llm = AsyncMock()
        v = VisionAnalyzer(llm, VisionConfig(enabled=False))
        result = await v.analyze_desktop("base64data")

        assert result.success is False
        assert "nicht aktiviert" in result.error
        llm.chat.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_empty_screenshot_returns_error(self):
        v, _ = self._make_analyzer("")
        result = await v.analyze_desktop("")

        assert result.success is False
        assert "Kein Screenshot" in result.error

    @pytest.mark.asyncio
    async def test_task_context_appended_to_prompt(self):
        v, llm = self._make_analyzer('{"elements": []}')
        await v.analyze_desktop("base64data", task_context="Reddit oeffnen")

        call_args = llm.chat.call_args
        messages = call_args.kwargs.get("messages", call_args[1].get("messages", []))
        # The prompt should contain the context
        msg_content = str(messages)
        assert "Reddit" in msg_content

    @pytest.mark.asyncio
    async def test_llm_error_handled(self):
        llm = AsyncMock()
        llm.chat = AsyncMock(side_effect=RuntimeError("GPU OOM"))
        cfg = VisionConfig(enabled=True, model="qwen3-vl:32b", backend_type="ollama")
        v = VisionAnalyzer(llm, cfg)

        result = await v.analyze_desktop("base64data")
        assert result.success is False
        assert "fehlgeschlagen" in result.error

    @pytest.mark.asyncio
    async def test_non_json_response_returns_description_no_elements(self):
        v, _ = self._make_analyzer("I see a calculator and a browser window.")
        result = await v.analyze_desktop("base64data")

        assert result.success is True
        assert "calculator" in result.description
        assert result.elements == []  # No JSON → no structured elements

    @pytest.mark.asyncio
    async def test_custom_prompt_overrides_default(self):
        v, llm = self._make_analyzer('{"elements": []}')
        await v.analyze_desktop("base64data", prompt="Custom prompt here")

        call_args = llm.chat.call_args
        messages = str(call_args)
        assert "Custom prompt" in messages

    @pytest.mark.asyncio
    async def test_stats_updated(self):
        v, _ = self._make_analyzer('{"elements": []}')
        assert v.stats()["calls"] == 0

        await v.analyze_desktop("base64data")
        assert v.stats()["calls"] == 1
```

### Test 4: `computer_screenshot` — Returns Elements

```python
class TestComputerScreenshotWithVision:
    @pytest.mark.asyncio
    async def test_elements_in_result(self):
        from jarvis.mcp.computer_use import ComputerUseTools
        from jarvis.browser.vision import VisionAnalysisResult
        from unittest.mock import AsyncMock, MagicMock, patch

        mock_vision = AsyncMock()
        mock_vision.analyze_desktop = AsyncMock(return_value=VisionAnalysisResult(
            success=True,
            description="Desktop mit Rechner",
            elements=[{"name": "Rechner", "type": "window", "x": 200, "y": 300,
                        "w": 400, "h": 500, "text": "", "clickable": True}],
        ))

        tools = ComputerUseTools(vision_analyzer=mock_vision)

        with patch("jarvis.mcp.computer_use._take_screenshot_b64",
                    return_value=("base64", 1920, 1080)):
            result = await tools.computer_screenshot()

        assert result["success"] is True
        assert len(result["elements"]) == 1
        assert result["elements"][0]["name"] == "Rechner"
        assert "Rechner" in result["description"]
        mock_vision.analyze_desktop.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_no_vision_returns_empty_elements(self):
        from jarvis.mcp.computer_use import ComputerUseTools
        from unittest.mock import patch

        tools = ComputerUseTools(vision_analyzer=None)

        with patch("jarvis.mcp.computer_use._take_screenshot_b64",
                    return_value=("base64", 1920, 1080)):
            result = await tools.computer_screenshot()

        assert result["success"] is True
        assert result["elements"] == []
        assert "No vision" in result["description"]

    @pytest.mark.asyncio
    async def test_vision_error_returns_empty_elements(self):
        from jarvis.mcp.computer_use import ComputerUseTools
        from jarvis.browser.vision import VisionAnalysisResult
        from unittest.mock import AsyncMock, patch

        mock_vision = AsyncMock()
        mock_vision.analyze_desktop = AsyncMock(return_value=VisionAnalysisResult(
            success=False, error="GPU timeout",
        ))

        tools = ComputerUseTools(vision_analyzer=mock_vision)

        with patch("jarvis.mcp.computer_use._take_screenshot_b64",
                    return_value=("base64", 1920, 1080)):
            result = await tools.computer_screenshot()

        assert result["success"] is True  # Screenshot itself succeeded
        assert result["elements"] == []
        assert "GPU timeout" in result["description"]

    @pytest.mark.asyncio
    async def test_task_context_passed_through(self):
        from jarvis.mcp.computer_use import ComputerUseTools
        from jarvis.browser.vision import VisionAnalysisResult
        from unittest.mock import AsyncMock, patch

        mock_vision = AsyncMock()
        mock_vision.analyze_desktop = AsyncMock(return_value=VisionAnalysisResult(
            success=True, description="OK", elements=[],
        ))

        tools = ComputerUseTools(vision_analyzer=mock_vision)

        with patch("jarvis.mcp.computer_use._take_screenshot_b64",
                    return_value=("base64", 1920, 1080)):
            await tools.computer_screenshot(task_context="Reddit oeffnen")

        mock_vision.analyze_desktop.assert_awaited_once()
        call_kwargs = mock_vision.analyze_desktop.call_args
        assert call_kwargs.kwargs.get("task_context") == "Reddit oeffnen" or \
               "Reddit" in str(call_kwargs)
```

### Test 5: Executor Vision Focus

```python
class TestExecutorVisionFocus:
    @pytest.mark.asyncio
    async def test_vision_focus_clicks_window(self):
        """After exec_command with CU tools, executor should screenshot + click window."""
        from unittest.mock import AsyncMock, MagicMock
        from jarvis.core.executor import Executor
        from jarvis.models import PlannedAction, GateDecision, GateStatus

        config = MagicMock()
        config.executor = MagicMock(
            default_timeout_seconds=30, max_retries=1,
            backoff_base_delay_seconds=0.1, max_output_chars=10000,
            max_parallel_tools=4,
        )
        mcp = MagicMock()

        # Mock screenshot handler returns elements
        screenshot_handler = AsyncMock(return_value={
            "success": True, "width": 1920, "height": 1080,
            "description": "Desktop", "elements": [
                {"name": "Rechner", "type": "window", "x": 200, "y": 300, "clickable": True},
            ],
        })
        click_handler = AsyncMock(return_value={"success": True})
        exec_handler = AsyncMock(return_value=MagicMock(
            content="OK", is_error=False, success=True,
        ))

        mcp._builtin_handlers = {
            "computer_screenshot": screenshot_handler,
            "computer_click": click_handler,
            "exec_command": exec_handler,
        }
        mcp.call_tool = AsyncMock()

        # ... (executor test with computer_use actions verifying click is called)
```

### Test 6: Gatekeeper Classification Unchanged

```python
class TestGatekeeperCUClassification:
    def test_screenshot_green_actions_yellow(self):
        from jarvis.core.gatekeeper import Gatekeeper
        from jarvis.config import JarvisConfig, ToolsConfig
        from jarvis.models import PlannedAction

        config = JarvisConfig(tools=ToolsConfig(computer_use_enabled=True))
        gk = Gatekeeper(config)

        # Screenshot is GREEN (read-only)
        action = PlannedAction(tool="computer_screenshot", params={}, rationale="test")
        assert gk._classify_risk(action).name == "GREEN"

        # Actions are YELLOW
        for tool in ["computer_click", "computer_type", "computer_hotkey"]:
            action = PlannedAction(tool=tool, params={}, rationale="test")
            assert gk._classify_risk(action).name == "YELLOW"
```

## Files Changed

| File | Change |
|---|---|
| `src/jarvis/browser/vision.py` | + `analyze_desktop()`, + `_parse_desktop_elements()`, + `_validate_elements()`, + desktop prompt constants |
| `src/jarvis/mcp/computer_use.py` | Replace hasattr vision call with `analyze_desktop()`, return elements, add `task_context` param |
| `src/jarvis/core/executor.py` | Replace PowerShell focus with vision-based screenshot→click |
| `src/jarvis/core/planner.py` | Updated CU instructions and few-shot example |
| `tests/test_browser/test_vision.py` | + `TestAnalyzeDesktop` (8 tests), + `TestParseDesktopElements` (5 tests), + `TestValidateElements` (4 tests) |
| `tests/unit/test_knowledge_builder.py` or new test file | + `TestComputerScreenshotWithVision` (4 tests), + `TestExecutorVisionFocus` (1 test), + `TestGatekeeperCUClassification` (1 test) |

## What Does NOT Change

- `core/vision.py` — message building, backend formatting (identical for browser and desktop)
- `core/unified_llm.py` — LLM client (unchanged)
- `gateway/phases/tools.py` — VisionAnalyzer creation (unchanged, same instance used)
- Sequential CU execution (`max_parallel=1`)
- Clipboard paste for typing
- Security model (screenshot=GREEN, actions=YELLOW)
- Verification screenshot + REPLAN block in gateway.py
- Multi-monitor screenshot support

## Expected Outcome

After implementation:
1. `computer_screenshot` returns structured UI elements with pixel coordinates
2. The planner uses coordinates for targeted clicks instead of blind typing
3. Window focusing works via vision+click (no PowerShell)
4. Verification screenshots describe what the vision model actually sees
5. The calculator test: open → screenshot sees Rechner → click on it → type → verify screenshot shows result
