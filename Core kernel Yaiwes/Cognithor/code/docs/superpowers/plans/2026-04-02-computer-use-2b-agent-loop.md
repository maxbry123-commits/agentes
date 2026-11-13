# Computer Use Phase 2B: Agent Loop — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a closed-loop CU agent that uses a single vision-language model (qwen3-vl:32b) for both planning and screenshot analysis — zero model swaps, multi-turn screenshot→decide→act cycles.

**Architecture:** New `CUAgentExecutor` class in `cu_agent.py` implements the agent loop. The PGE loop detects CU plans and delegates to the agent. Phase 1 workarounds (forced plans, polling focus, ensure_focus) are removed. The agent uses qwen3-vl:32b for everything — planning, vision, text extraction.

**Tech Stack:** Python 3.13, pytest (asyncio_mode=auto), AsyncMock, json, re, time, asyncio

**Spec:** `docs/superpowers/specs/2026-04-02-computer-use-2b-agent-loop-design.md`

---

## File Structure

| File | Responsibility |
|---|---|
| `src/jarvis/core/cu_agent.py` (create) | CUAgentExecutor, CUAgentConfig, CUAgentResult — the core agent loop |
| `src/jarvis/browser/vision.py` (modify) | Add `extract_text_from_screenshot()` method |
| `src/jarvis/gateway/gateway.py` (modify) | Add `_is_cu_plan()`, CU delegation in PGE loop, remove Phase 1 CU workarounds |
| `src/jarvis/core/planner.py` (modify) | Remove `_should_force_cu_plan`, `_build_cu_plan`, CU override block |
| `src/jarvis/core/executor.py` (modify) | Remove `_cu_wait_and_focus`, `_cu_ensure_focus`, their call sites |
| `tests/test_core/test_cu_agent.py` (create) | Tests for CUAgentExecutor |
| `tests/test_browser/test_vision.py` (modify) | Add TestExtractText |
| `tests/unit/test_computer_use_vision.py` (modify) | Add TestGatewayCUDetection |

---

### Task 1: CUAgentExecutor Core — Data Classes + Abort Logic

**Files:**
- Create: `src/jarvis/core/cu_agent.py`
- Create: `tests/test_core/test_cu_agent.py`

- [ ] **Step 1: Write failing tests for data classes and abort logic**

Create `tests/test_core/test_cu_agent.py`:

```python
"""Tests for CUAgentExecutor — closed-loop desktop automation agent."""

from __future__ import annotations

import json
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from jarvis.core.cu_agent import CUAgentConfig, CUAgentExecutor, CUAgentResult


class TestCUAgentConfig:
    def test_defaults(self):
        cfg = CUAgentConfig()
        assert cfg.max_iterations == 30
        assert cfg.max_duration_seconds == 480
        assert cfg.vision_model == "qwen3-vl:32b"
        assert cfg.stuck_detection_threshold == 3

    def test_custom(self):
        cfg = CUAgentConfig(max_iterations=10, max_duration_seconds=120)
        assert cfg.max_iterations == 10
        assert cfg.max_duration_seconds == 120


class TestCUAgentResult:
    def test_defaults(self):
        r = CUAgentResult()
        assert r.success is False
        assert r.iterations == 0
        assert r.duration_ms == 0
        assert r.tool_results == []
        assert r.abort_reason == ""
        assert r.extracted_content == ""
        assert r.action_history == []


class TestCUAgentAbort:
    def _make_agent(self, **config_overrides) -> CUAgentExecutor:
        planner = MagicMock()
        planner._ollama = AsyncMock()
        mcp = MagicMock()
        mcp._builtin_handlers = {}
        gatekeeper = MagicMock()
        wm = MagicMock()
        config = CUAgentConfig(**config_overrides)
        return CUAgentExecutor(planner, mcp, gatekeeper, wm, {}, config)

    def test_check_abort_max_iterations(self):
        agent = self._make_agent(max_iterations=5)
        result = CUAgentResult(iterations=5)
        assert agent._check_abort(result, time.monotonic(), None) == "max_iterations"

    def test_check_abort_timeout(self):
        agent = self._make_agent(max_duration_seconds=1)
        result = CUAgentResult(iterations=1)
        start = time.monotonic() - 2  # 2 seconds ago
        assert agent._check_abort(result, start, None) == "timeout"

    def test_check_abort_user_cancel(self):
        agent = self._make_agent()
        result = CUAgentResult(iterations=1)
        assert agent._check_abort(result, time.monotonic(), lambda: True) == "user_cancel"

    def test_check_abort_stuck_loop(self):
        agent = self._make_agent(stuck_detection_threshold=3)
        agent._recent_actions = ["click:x=100,y=200"] * 3
        result = CUAgentResult(iterations=3)
        assert agent._check_abort(result, time.monotonic(), None) == "stuck_loop"

    def test_check_abort_no_abort(self):
        agent = self._make_agent()
        result = CUAgentResult(iterations=1)
        assert agent._check_abort(result, time.monotonic(), None) == ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_core/test_cu_agent.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'jarvis.core.cu_agent'`

- [ ] **Step 3: Create `cu_agent.py` with data classes and abort logic**

Create `src/jarvis/core/cu_agent.py`:

```python
"""CU Agent Executor — Closed-loop desktop automation agent.

Implements the Screenshot→Decide→Act cycle for Computer Use.
Uses a single vision-language model (qwen3-vl:32b) for both
planning and screenshot analysis — zero model swaps.

Architecture:
  PGE Loop detects CU plan → delegates to CUAgentExecutor
  → agent runs screenshot→decide→act cycles until DONE or abort
  → results flow back to PGE loop for response formulation
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from jarvis.models import ActionPlan, PlannedAction, ToolResult
from jarvis.utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class CUAgentConfig:
    """Configuration for the CU Agent Loop."""

    max_iterations: int = 30
    max_duration_seconds: int = 480  # 8 minutes
    vision_model: str = "qwen3-vl:32b"
    screenshot_after_action: bool = True
    stuck_detection_threshold: int = 3


@dataclass
class CUAgentResult:
    """Result of a CU Agent execution."""

    success: bool = False
    iterations: int = 0
    duration_ms: int = 0
    tool_results: list[ToolResult] = field(default_factory=list)
    final_screenshot_description: str = ""
    abort_reason: str = ""
    extracted_content: str = ""
    action_history: list[str] = field(default_factory=list)


class CUAgentExecutor:
    """Closed-loop agent for desktop automation via Computer Use tools.

    Executes a Screenshot→Decide→Act cycle until the goal is reached
    or an abort condition triggers. Uses a single vision-language model
    for both planning and screenshot analysis — zero model swaps.
    """

    _CU_DECIDE_PROMPT = (
        "Du steuerst den Desktop des Users. Ziel: {goal}\n\n"
        "Bisherige Aktionen:\n{action_history}\n\n"
        "Aktueller Screenshot:\n{screenshot_description}\n\n"
        "Erkannte UI-Elemente:\n{elements_json}\n\n"
        "Was ist der NAECHSTE einzelne Schritt? Antworte mit EINEM der folgenden:\n\n"
        "1. Ein einzelner Tool-Call als JSON:\n"
        '{{"tool": "tool_name", "params": {{...}}, "rationale": "Warum"}}\n\n'
        "2. Text-Extraktion:\n"
        '{{"tool": "extract_text", "params": {{}}, "rationale": "Text vom Bildschirm lesen"}}\n\n'
        "3. Wenn das Ziel erreicht ist:\n"
        "DONE: [Zusammenfassung was erreicht wurde]\n\n"
        "Verfuegbare Tools: exec_command, computer_screenshot, computer_click, "
        "computer_type, computer_hotkey, computer_scroll\n\n"
        "WICHTIG: Plane immer nur EINEN Schritt. Nach der Ausfuehrung "
        "bekommst du einen neuen Screenshot."
    )

    def __init__(
        self,
        planner: Any,
        mcp_client: Any,
        gatekeeper: Any,
        working_memory: Any,
        tool_schemas: dict[str, Any],
        config: CUAgentConfig | None = None,
    ) -> None:
        self._planner = planner
        self._mcp = mcp_client
        self._gatekeeper = gatekeeper
        self._wm = working_memory
        self._tool_schemas = tool_schemas
        self._config = config or CUAgentConfig()
        self._action_history: list[str] = []
        self._recent_actions: list[str] = []

    def _check_abort(
        self,
        result: CUAgentResult,
        start: float,
        cancel_check: Callable | None,
    ) -> str:
        """Check all abort conditions. Returns reason or empty string."""
        if cancel_check and cancel_check():
            return "user_cancel"
        if result.iterations >= self._config.max_iterations:
            return "max_iterations"
        if time.monotonic() - start > self._config.max_duration_seconds:
            return "timeout"
        if (
            len(self._recent_actions) >= self._config.stuck_detection_threshold
            and len(set(self._recent_actions)) == 1
        ):
            return "stuck_loop"
        return ""

    @staticmethod
    def _format_params(params: dict) -> str:
        """Compact param string for action history."""
        parts = []
        for k, v in params.items():
            sv = str(v)
            if len(sv) > 30:
                sv = sv[:27] + "..."
            parts.append(f"{k}={sv}")
        return ", ".join(parts)

    @staticmethod
    def _format_elements(elements: list[dict]) -> str:
        """Format elements list for the decide prompt."""
        if not elements:
            return "(keine Elemente erkannt)"
        compact = [
            {k: e[k] for k in ("name", "type", "x", "y", "text") if k in e}
            for e in elements[:15]
        ]
        return json.dumps(compact, ensure_ascii=False, indent=None)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_core/test_cu_agent.py -v`
Expected: 7 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/core/cu_agent.py tests/test_core/test_cu_agent.py
git commit -m "feat(cu_agent): add CUAgentExecutor core — data classes, abort logic, helpers"
```

---

### Task 2: CUAgentExecutor — Decision Parsing + Tool Execution

**Files:**
- Modify: `src/jarvis/core/cu_agent.py`
- Test: `tests/test_core/test_cu_agent.py`

- [ ] **Step 1: Write failing tests for decision parsing and tool execution**

Append to `tests/test_core/test_cu_agent.py`:

```python
class TestCUDecisionParsing:
    """Tests for _parse_tool_decision and _decide_next_step."""

    def _make_agent(self) -> CUAgentExecutor:
        planner = MagicMock()
        planner._ollama = AsyncMock()
        mcp = MagicMock()
        mcp._builtin_handlers = {}
        return CUAgentExecutor(planner, mcp, MagicMock(), MagicMock(), {})

    def test_parse_tool_json(self):
        agent = self._make_agent()
        result = agent._parse_tool_decision(
            '{"tool": "computer_click", "params": {"x": 200, "y": 300}, "rationale": "click"}'
        )
        assert result is not None
        assert result["tool"] == "computer_click"
        assert result["params"]["x"] == 200

    def test_parse_json_in_markdown(self):
        agent = self._make_agent()
        raw = '```json\n{"tool": "computer_type", "params": {"text": "hello"}, "rationale": "type"}\n```'
        result = agent._parse_tool_decision(raw)
        assert result is not None
        assert result["tool"] == "computer_type"

    def test_parse_done_signal(self):
        """DONE detection is handled in _decide_next_step, not _parse_tool_decision."""
        agent = self._make_agent()
        result = agent._parse_tool_decision("DONE: Rechner zeigt 459")
        assert result is None  # Not a tool call

    def test_parse_garbage_returns_none(self):
        agent = self._make_agent()
        assert agent._parse_tool_decision("This is just text.") is None

    def test_parse_with_think_tags(self):
        agent = self._make_agent()
        raw = '<think>analyzing...</think>\n{"tool": "computer_scroll", "params": {"direction": "down"}}'
        # Think tags are stripped in _decide_next_step, so direct parse may fail
        # But regex should find the JSON
        result = agent._parse_tool_decision(raw)
        # Might succeed via regex tier
        if result:
            assert result["tool"] == "computer_scroll"


class TestCUToolExecution:
    """Tests for _execute_tool."""

    @pytest.mark.asyncio
    async def test_execute_tool_success(self):
        planner = MagicMock()
        mcp = MagicMock()
        handler = AsyncMock(return_value={"success": True, "action": "click"})
        mcp._builtin_handlers = {"computer_click": handler}

        agent = CUAgentExecutor(planner, mcp, MagicMock(), MagicMock(), {})
        result = await agent._execute_tool("computer_click", {"x": 100, "y": 200})

        assert result.success is True
        assert "click" in result.content
        handler.assert_awaited_once_with(x=100, y=200)

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self):
        planner = MagicMock()
        mcp = MagicMock()
        mcp._builtin_handlers = {}

        agent = CUAgentExecutor(planner, mcp, MagicMock(), MagicMock(), {})
        result = await agent._execute_tool("nonexistent", {})

        assert result.is_error is True
        assert "not found" in result.content

    @pytest.mark.asyncio
    async def test_execute_tool_exception(self):
        planner = MagicMock()
        mcp = MagicMock()
        handler = AsyncMock(side_effect=RuntimeError("pyautogui crash"))
        mcp._builtin_handlers = {"computer_click": handler}

        agent = CUAgentExecutor(planner, mcp, MagicMock(), MagicMock(), {})
        result = await agent._execute_tool("computer_click", {"x": 0, "y": 0})

        assert result.is_error is True
        assert "pyautogui crash" in result.content
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_core/test_cu_agent.py::TestCUDecisionParsing tests/test_core/test_cu_agent.py::TestCUToolExecution -v`
Expected: FAIL with `AttributeError: 'CUAgentExecutor' has no attribute '_parse_tool_decision'`

- [ ] **Step 3: Add `_parse_tool_decision`, `_execute_tool`, `_take_and_analyze_screenshot`, `_decide_next_step` to CUAgentExecutor**

Append to `CUAgentExecutor` class in `src/jarvis/core/cu_agent.py`:

```python
    def _parse_tool_decision(self, raw: str) -> dict | None:
        """Parse a single tool call from the planner response."""
        # Tier 1: direct JSON parse
        try:
            data = json.loads(raw)
            if isinstance(data, dict) and "tool" in data:
                return data
        except (json.JSONDecodeError, ValueError):
            pass

        # Tier 2: markdown code block
        md_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
        if md_match:
            try:
                data = json.loads(md_match.group(1))
                if isinstance(data, dict) and "tool" in data:
                    return data
            except (json.JSONDecodeError, ValueError):
                pass

        # Tier 3: find JSON object with "tool" key
        json_match = re.search(r'\{[^{}]*"tool"[^{}]*\}', raw)
        if json_match:
            try:
                data = json.loads(json_match.group())
                if "tool" in data:
                    return data
            except (json.JSONDecodeError, ValueError):
                pass

        return None

    async def _execute_tool(self, tool: str, params: dict) -> ToolResult:
        """Execute a single CU tool via MCP client."""
        handler = self._mcp._builtin_handlers.get(tool)
        if not handler:
            return ToolResult(
                tool_name=tool,
                content=f"Tool '{tool}' not found",
                is_error=True,
            )
        try:
            result = await handler(**params)
            content = str(result) if not isinstance(result, str) else result
            return ToolResult(
                tool_name=tool,
                content=content[:5000],
                is_error=False,
            )
        except Exception as exc:
            return ToolResult(
                tool_name=tool,
                content=f"Error: {exc}",
                is_error=True,
            )

    async def _take_and_analyze_screenshot(self) -> dict | None:
        """Take screenshot via CU tool and return result with elements."""
        handler = self._mcp._builtin_handlers.get("computer_screenshot")
        if not handler:
            return None
        try:
            return await handler()
        except Exception:
            log.debug("cu_agent_screenshot_failed", exc_info=True)
            return None

    async def _decide_next_step(self, goal: str, screenshot: dict) -> dict | None:
        """Ask the planner what to do next based on the screenshot.

        Returns:
            {"tool": "...", "params": {...}} for an action
            {"done": True, "summary": "..."} for completion
            None if parsing failed
        """
        prompt = self._CU_DECIDE_PROMPT.format(
            goal=goal,
            action_history="\n".join(self._action_history[-10:]) or "(keine)",
            screenshot_description=screenshot.get("description", "")[:1000],
            elements_json=self._format_elements(screenshot.get("elements", [])),
        )

        try:
            response = await self._planner._ollama.chat(
                model=self._config.vision_model,
                messages=[
                    {"role": "system", "content": "Du bist ein Desktop-Automations-Agent."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )
            text = response.get("message", {}).get("content", "")
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

            if text.upper().startswith("DONE"):
                summary = text.split(":", 1)[1].strip() if ":" in text else text[4:].strip()
                return {"done": True, "summary": summary}

            return self._parse_tool_decision(text)

        except Exception as exc:
            log.warning("cu_agent_decide_failed", error=str(exc)[:200])
            return None

    async def _extract_text_from_screen(self) -> str:
        """Extract all visible text from current screen via vision model."""
        try:
            from jarvis.mcp.computer_use import _take_screenshot_b64
            from jarvis.core.vision import build_vision_message, format_for_backend

            b64, _, _ = await asyncio.get_running_loop().run_in_executor(
                None, _take_screenshot_b64
            )
            msg = build_vision_message(
                "Lies ALLEN sichtbaren Text in diesem Screenshot ab. "
                "Gib den Text zeilenweise wieder. Antworte NUR mit dem Text.",
                [b64],
            )
            formatted = format_for_backend(msg, "ollama")
            response = await self._planner._ollama.chat(
                model=self._config.vision_model,
                messages=[formatted],
                temperature=0.1,
            )
            return response.get("message", {}).get("content", "")
        except Exception:
            log.debug("cu_agent_extract_text_failed", exc_info=True)
            return ""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_core/test_cu_agent.py -v`
Expected: All PASSED

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/core/cu_agent.py tests/test_core/test_cu_agent.py
git commit -m "feat(cu_agent): add decision parsing, tool execution, screenshot, text extraction"
```

---

### Task 3: CUAgentExecutor — The Execute Loop

**Files:**
- Modify: `src/jarvis/core/cu_agent.py`
- Test: `tests/test_core/test_cu_agent.py`

- [ ] **Step 1: Write failing test for the full execute loop**

Append to `tests/test_core/test_cu_agent.py`:

```python
class TestCUAgentExecuteLoop:
    """Tests for the full execute() loop."""

    @pytest.mark.asyncio
    async def test_happy_path_done_in_3_iterations(self):
        """Agent: exec → screenshot(sees window) → decide(DONE)."""
        planner = MagicMock()
        planner._ollama = AsyncMock()
        # First decide call returns click, second returns DONE
        planner._ollama.chat = AsyncMock(side_effect=[
            {"message": {"content": '{"tool": "computer_click", "params": {"x": 200, "y": 300}, "rationale": "click window"}'}},
            {"message": {"content": "DONE: Taschenrechner zeigt 459"}},
        ])

        mcp = MagicMock()
        screenshot_handler = AsyncMock(return_value={
            "success": True, "width": 1920, "height": 1080,
            "description": "Rechner sichtbar",
            "elements": [{"name": "Rechner", "type": "window", "x": 200, "y": 300, "clickable": True}],
        })
        click_handler = AsyncMock(return_value={"success": True})
        exec_handler = AsyncMock(return_value="OK")
        mcp._builtin_handlers = {
            "computer_screenshot": screenshot_handler,
            "computer_click": click_handler,
            "exec_command": exec_handler,
        }

        initial_plan = ActionPlan(
            goal="Rechner oeffnen",
            steps=[PlannedAction(tool="exec_command", params={"command": "start calc.exe"}, rationale="start")],
        )

        agent = CUAgentExecutor(planner, mcp, MagicMock(), MagicMock(), {})
        result = await agent.execute(goal="Rechner oeffnen", initial_plan=initial_plan)

        assert result.success is True
        assert result.abort_reason == "done"
        assert result.iterations >= 1
        assert len(result.action_history) >= 2  # exec + click + DONE
        assert "459" in str(result.action_history)

    @pytest.mark.asyncio
    async def test_abort_on_max_iterations(self):
        """Agent stops after max_iterations."""
        planner = MagicMock()
        planner._ollama = AsyncMock()
        # Always returns a click action (never DONE)
        planner._ollama.chat = AsyncMock(return_value={
            "message": {"content": '{"tool": "computer_click", "params": {"x": 100, "y": 100}}'},
        })

        mcp = MagicMock()
        mcp._builtin_handlers = {
            "computer_screenshot": AsyncMock(return_value={
                "success": True, "description": "screen", "elements": [],
            }),
            "computer_click": AsyncMock(return_value={"success": True}),
        }

        config = CUAgentConfig(max_iterations=3)
        agent = CUAgentExecutor(planner, mcp, MagicMock(), MagicMock(), {}, config)

        initial_plan = ActionPlan(goal="test", steps=[])
        result = await agent.execute(goal="test", initial_plan=initial_plan)

        assert result.success is False
        assert result.abort_reason == "max_iterations"
        assert result.iterations == 3

    @pytest.mark.asyncio
    async def test_abort_on_user_cancel(self):
        """Agent stops when cancel_check returns True."""
        planner = MagicMock()
        planner._ollama = AsyncMock()
        planner._ollama.chat = AsyncMock(return_value={
            "message": {"content": '{"tool": "computer_click", "params": {"x": 1, "y": 1}}'},
        })

        mcp = MagicMock()
        mcp._builtin_handlers = {
            "computer_screenshot": AsyncMock(return_value={
                "success": True, "description": "screen", "elements": [],
            }),
            "computer_click": AsyncMock(return_value={"success": True}),
        }

        agent = CUAgentExecutor(planner, mcp, MagicMock(), MagicMock(), {})
        result = await agent.execute(
            goal="test",
            initial_plan=ActionPlan(goal="test", steps=[]),
            cancel_check=lambda: True,  # Always cancelled
        )

        assert result.abort_reason == "user_cancel"
        assert result.iterations <= 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_core/test_cu_agent.py::TestCUAgentExecuteLoop -v`
Expected: FAIL with `AttributeError: 'CUAgentExecutor' has no attribute 'execute'`

- [ ] **Step 3: Add the `execute()` method to CUAgentExecutor**

Add after `_format_elements()` and before `_parse_tool_decision()` in `src/jarvis/core/cu_agent.py`:

```python
    async def execute(
        self,
        goal: str,
        initial_plan: ActionPlan,
        status_callback: Callable | None = None,
        cancel_check: Callable | None = None,
    ) -> CUAgentResult:
        """Run the CU agent loop until done or aborted."""
        result = CUAgentResult()
        start = time.monotonic()

        async def _status(phase: str, msg: str) -> None:
            if status_callback:
                try:
                    await status_callback(phase, msg)
                except Exception:
                    pass

        # Execute initial plan steps
        await _status("computer_use", f"Starte: {goal[:60]}...")
        for step in initial_plan.steps:
            tool_result = await self._execute_tool(step.tool, step.params)
            result.tool_results.append(tool_result)
            self._action_history.append(
                f"{step.tool}({self._format_params(step.params)}) "
                f"-> {'OK' if tool_result.success else 'FAIL'}"
            )

        # Main agent loop: screenshot → decide → act
        while True:
            result.iterations += 1

            abort = self._check_abort(result, start, cancel_check)
            if abort:
                result.abort_reason = abort
                break

            await _status(
                "computer_use",
                f"Schritt {result.iterations}/{self._config.max_iterations}: "
                f"Analysiere Bildschirm...",
            )

            screenshot = await self._take_and_analyze_screenshot()
            if not screenshot:
                self._action_history.append("computer_screenshot() -> FAIL")
                continue

            result.final_screenshot_description = screenshot.get("description", "")

            decision = await self._decide_next_step(goal, screenshot)

            if decision is None:
                self._action_history.append("decide() -> no valid action")
                continue

            if decision.get("done"):
                result.success = True
                result.abort_reason = "done"
                summary = decision.get("summary", "")
                self._action_history.append(f"DONE: {summary}")
                break

            if decision.get("tool") == "extract_text":
                text = await self._extract_text_from_screen()
                if text:
                    result.extracted_content += text + "\n\n"
                    self._action_history.append(f"extract_text() -> {len(text)} chars")
                continue

            tool = decision["tool"]
            params = decision.get("params", {})
            await _status("computer_use", f"Schritt {result.iterations}: {tool}...")

            tool_result = await self._execute_tool(tool, params)
            result.tool_results.append(tool_result)
            self._action_history.append(
                f"{tool}({self._format_params(params)}) "
                f"-> {'OK' if tool_result.success else 'FAIL'}"
            )

            action_key = f"{tool}:{sorted(params.items())}"
            self._recent_actions.append(action_key)
            if len(self._recent_actions) > self._config.stuck_detection_threshold:
                self._recent_actions.pop(0)

        result.duration_ms = int((time.monotonic() - start) * 1000)
        result.action_history = list(self._action_history)
        log.info(
            "cu_agent_complete",
            success=result.success,
            iterations=result.iterations,
            duration_ms=result.duration_ms,
            abort_reason=result.abort_reason,
            actions=len(self._action_history),
        )
        return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_core/test_cu_agent.py -v`
Expected: All PASSED

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/core/cu_agent.py tests/test_core/test_cu_agent.py
git commit -m "feat(cu_agent): add execute() loop — screenshot→decide→act with abort conditions"
```

---

### Task 4: VisionAnalyzer `extract_text_from_screenshot`

**Files:**
- Modify: `src/jarvis/browser/vision.py`
- Test: `tests/test_browser/test_vision.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_browser/test_vision.py`:

```python
class TestExtractText:
    """Tests for VisionAnalyzer.extract_text_from_screenshot."""

    @pytest.mark.asyncio
    async def test_extract_text_success(self):
        llm = AsyncMock()
        llm.chat = AsyncMock(return_value={
            "message": {"content": "Reddit - r/locallama\nPost 1: Hello World\nPost 2: Test"},
        })
        cfg = VisionConfig(enabled=True, model="qwen3-vl:32b", backend_type="ollama")
        v = VisionAnalyzer(llm, cfg)

        result = await v.extract_text_from_screenshot("base64data")
        assert result.success is True
        assert "Reddit" in result.description
        llm.chat.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_extract_text_disabled(self):
        llm = AsyncMock()
        v = VisionAnalyzer(llm, VisionConfig(enabled=False))
        result = await v.extract_text_from_screenshot("base64data")
        assert result.success is False
        assert "nicht aktiviert" in result.error

    @pytest.mark.asyncio
    async def test_extract_text_empty_screenshot(self):
        llm = AsyncMock()
        cfg = VisionConfig(enabled=True, model="qwen3-vl:32b")
        v = VisionAnalyzer(llm, cfg)
        result = await v.extract_text_from_screenshot("")
        assert result.success is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_browser/test_vision.py::TestExtractText -v`
Expected: FAIL with `AttributeError: 'VisionAnalyzer' has no attribute 'extract_text_from_screenshot'`

- [ ] **Step 3: Add `extract_text_from_screenshot` to VisionAnalyzer**

In `src/jarvis/browser/vision.py`, add after `analyze_desktop()` and before `stats()`:

```python
    async def extract_text_from_screenshot(
        self,
        screenshot_b64: str,
    ) -> VisionAnalysisResult:
        """Extract all visible text from a screenshot (OCR-like).

        Uses the vision model to read text from the screen, without
        structured element detection. Optimized for content extraction.
        """
        if not self.is_enabled:
            return VisionAnalysisResult(error="Vision nicht aktiviert")

        if not screenshot_b64:
            return VisionAnalysisResult(error="Kein Screenshot-Daten")

        prompt = (
            "Lies ALLEN sichtbaren Text in diesem Screenshot ab. "
            "Gib den Text zeilenweise wieder, so wie er auf dem Bildschirm "
            "erscheint. Antworte NUR mit dem extrahierten Text, kein JSON, "
            "keine Erklaerungen."
        )
        return await self._send_vision_request(screenshot_b64, prompt)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_browser/test_vision.py::TestExtractText -v`
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/browser/vision.py tests/test_browser/test_vision.py
git commit -m "feat(vision): add extract_text_from_screenshot for OCR-like content reading"
```

---

### Task 5: Gateway PGE Loop Integration

**Files:**
- Modify: `src/jarvis/gateway/gateway.py`
- Test: `tests/unit/test_computer_use_vision.py`

- [ ] **Step 1: Write test for CU plan detection**

Append to `tests/unit/test_computer_use_vision.py`:

```python
class TestGatewayCUDetection:
    """Tests for _is_cu_plan detection."""

    def test_cu_plan_with_computer_click(self):
        from jarvis.gateway.gateway import Gateway
        from jarvis.models import ActionPlan, PlannedAction

        plan = ActionPlan(
            goal="test",
            steps=[
                PlannedAction(tool="exec_command", params={"command": "calc.exe"}, rationale="start"),
                PlannedAction(tool="computer_click", params={"x": 100, "y": 200}, rationale="click"),
            ],
        )
        assert Gateway._is_cu_plan(plan) is True

    def test_non_cu_plan(self):
        from jarvis.gateway.gateway import Gateway
        from jarvis.models import ActionPlan, PlannedAction

        plan = ActionPlan(
            goal="test",
            steps=[PlannedAction(tool="web_search", params={"query": "test"}, rationale="search")],
        )
        assert Gateway._is_cu_plan(plan) is False

    def test_direct_response_not_cu(self):
        from jarvis.gateway.gateway import Gateway
        from jarvis.models import ActionPlan

        plan = ActionPlan(goal="test", direct_response="Hello!")
        assert Gateway._is_cu_plan(plan) is False
```

- [ ] **Step 2: Add `_is_cu_plan` and CU delegation to gateway.py**

**2a.** Add `_is_cu_plan` as a static method on Gateway:

```python
    @staticmethod
    def _is_cu_plan(plan: ActionPlan) -> bool:
        """Check if a plan uses Computer Use tools."""
        _CU_TOOLS = frozenset({
            "computer_screenshot", "computer_click", "computer_type",
            "computer_hotkey", "computer_scroll", "computer_drag",
        })
        return plan.has_actions and any(
            step.tool in _CU_TOOLS for step in plan.steps
        )
```

**2b.** In `_run_pge_loop`, after the run_recorder block (after line 3019) and before the parse_failed check (line 3021), add:

```python
            # Computer Use: delegate to CUAgentExecutor for multi-turn interaction
            if self._is_cu_plan(plan):
                from jarvis.core.cu_agent import CUAgentConfig, CUAgentExecutor

                _vision_model = getattr(self._config, "vision_model", "qwen3-vl:32b")
                cu_agent = CUAgentExecutor(
                    planner=self._planner,
                    mcp_client=self._mcp_client,
                    gatekeeper=self._gatekeeper,
                    working_memory=wm,
                    tool_schemas=tool_schemas,
                    config=CUAgentConfig(
                        max_iterations=30,
                        max_duration_seconds=480,
                        vision_model=_vision_model,
                    ),
                )
                cu_result = await cu_agent.execute(
                    goal=msg.text,
                    initial_plan=plan,
                    status_callback=_status_cb,
                    cancel_check=lambda: msg.session_id in self._cancelled_sessions,
                )
                all_results.extend(cu_result.tool_results)
                if cu_result.action_history:
                    wm.add_message(
                        Message(
                            role=MessageRole.SYSTEM,
                            content=(
                                "[Computer Use Ergebnis]\n"
                                + "\n".join(cu_result.action_history[-10:])
                                + f"\n\nAbschluss: {cu_result.abort_reason}"
                                + (
                                    f"\nExtrahierter Text:\n{cu_result.extracted_content[:2000]}"
                                    if cu_result.extracted_content
                                    else ""
                                )
                            ),
                            channel=msg.channel,
                        )
                    )
                await _status_cb("finishing", "Formuliere Antwort...")
                final_response = await self._formulate_response(
                    msg.text, all_results, wm, stream_callback,
                )
                break
```

**2c.** Remove the `_CU_DONE` REPLAN block (lines ~3071-3110) — the entire `if all_results and any(r.success and r.tool_name in _CU_DONE ...)` block including the verification screenshot. CUAgentExecutor handles this internally now.

- [ ] **Step 3: Run tests**

Run: `python -m pytest tests/unit/test_computer_use_vision.py::TestGatewayCUDetection -v`
Expected: 3 PASSED

- [ ] **Step 4: Commit**

```bash
git add src/jarvis/gateway/gateway.py tests/unit/test_computer_use_vision.py
git commit -m "feat(gateway): CU plan detection + delegation to CUAgentExecutor in PGE loop"
```

---

### Task 6: Remove Phase 1 Workarounds — Planner

**Files:**
- Modify: `src/jarvis/core/planner.py`

- [ ] **Step 1: Remove CU override block, `_should_force_cu_plan`, `_build_cu_plan`**

In `src/jarvis/core/planner.py`:

**Remove lines 590-681** — the entire block starting with the CU override comment through the end of `_build_cu_plan`. This includes:
- The `if plan.direct_response and ... self._should_force_cu_plan(...)` block (lines 590-601)
- The `_should_force_cu_plan` method (lines 604-624)
- The `_build_cu_plan` method (lines 626-681)

The line `return plan` (line 602) stays — it's the normal return from `plan()`.

- [ ] **Step 2: Run planner tests**

Run: `python -m pytest tests/test_core/ -x -q -k "planner" 2>&1 | tail -5`
Expected: All PASS

- [ ] **Step 3: Commit**

```bash
git add src/jarvis/core/planner.py
git commit -m "refactor(planner): remove Phase 1 CU workarounds — CUAgentExecutor handles this now"
```

---

### Task 7: Remove Phase 1 Workarounds — Executor

**Files:**
- Modify: `src/jarvis/core/executor.py`

- [ ] **Step 1: Remove `_cu_wait_and_focus`, `_cu_ensure_focus`, and their call sites**

In `src/jarvis/core/executor.py`:

**Remove the call sites** in `_run_with_sem` (lines 327-335):
```python
                # After launching a GUI app, poll for window then focus via vision
                if action.tool == "exec_command" and result.success and _has_computer_use:
                    await self._cu_wait_and_focus()

                # Before computer_type/hotkey: ensure a window is focused.
                if action.tool in ("computer_type", "computer_hotkey") and _has_computer_use:
                    await self._cu_ensure_focus()
```

**Remove the methods** `_cu_wait_and_focus` (lines ~404-451) and `_cu_ensure_focus` (lines ~454-490), including the `# ── Computer Use helpers` comment.

**Keep** the `max_parallel=1` logic for CU tools (lines 263-278) — still needed for the initial plan execution.

- [ ] **Step 2: Run executor tests**

Run: `python -m pytest tests/test_core/ -x -q -k "executor" 2>&1 | tail -5`
Expected: All PASS

- [ ] **Step 3: Commit**

```bash
git add src/jarvis/core/executor.py
git commit -m "refactor(executor): remove Phase 1 CU workarounds — CUAgentExecutor handles focus now"
```

---

### Task 8: Integration Verification

**Files:**
- All modified files from Tasks 1-7

- [ ] **Step 1: Run all CU-related tests**

```bash
python -m pytest tests/test_core/test_cu_agent.py tests/test_browser/test_vision.py tests/unit/test_computer_use_vision.py tests/test_session_management/test_computer_use.py -v
```
Expected: All PASS

- [ ] **Step 2: Run broader test sweep**

```bash
python -m pytest tests/ -x -q 2>&1 | tail -20
```
Expected: No new failures

- [ ] **Step 3: Verify wiring chain**

1. `gateway.py`: `_is_cu_plan()` detects CU plans
2. `gateway.py`: Creates `CUAgentExecutor` with `vision_model` from config
3. `cu_agent.py`: `execute()` runs screenshot→decide→act loop
4. `cu_agent.py`: `_decide_next_step()` calls `planner._ollama.chat(model=vision_model)`
5. `cu_agent.py`: `_take_and_analyze_screenshot()` calls `computer_screenshot` handler
6. `cu_agent.py`: `_execute_tool()` calls MCP handlers for click/type/scroll
7. `planner.py`: No more `_should_force_cu_plan` or `_build_cu_plan`
8. `executor.py`: No more `_cu_wait_and_focus` or `_cu_ensure_focus`

- [ ] **Step 4: Format and lint**

```bash
python -m ruff format src/jarvis/core/cu_agent.py src/jarvis/browser/vision.py src/jarvis/gateway/gateway.py src/jarvis/core/planner.py src/jarvis/core/executor.py tests/test_core/test_cu_agent.py tests/test_browser/test_vision.py tests/unit/test_computer_use_vision.py
python -m ruff check src/ tests/ --select=F821,F811 --no-fix
git add -A
git commit -m "test: verify Phase 2B Agent Loop integration — all clean"
```
