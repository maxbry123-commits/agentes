"""Browser Agent -- Autonomous browser control v17.

Orchestrates:
  - Playwright browser instance (headless)
  - PageAnalyzer for page understanding
  - SessionManager for cookie persistence
  - Multi-tab management
  - Workflow execution (step-by-step)
  - Automatic cookie banner detection
  - Screenshot on error
  - Content extraction

Requires: pip install playwright && playwright install chromium

OPTIONAL: Graceful degradation when Playwright is not installed.
"""

from __future__ import annotations

import asyncio
import base64
import contextlib
import time
from pathlib import Path
from typing import Any

from cognithor.browser.page_analyzer import PageAnalyzer
from cognithor.browser.session_manager import SessionManager
from cognithor.browser.types import (
    ActionResult,
    ActionType,
    BrowserAction,
    BrowserConfig,
    BrowserWorkflow,
    PageState,
    WorkflowStatus,
)
from cognithor.utils.logging import get_logger

log = get_logger(__name__)

# Check Playwright availability
_HAS_PLAYWRIGHT = False
try:
    from playwright.async_api import Browser, BrowserContext, Page, async_playwright  # noqa: F401

    _HAS_PLAYWRIGHT = True
except ImportError:
    pass


class BrowserAgent:
    """Autonomous browser agent -- controls web pages via Playwright.

    Usage:
        agent = BrowserAgent()
        await agent.start()
        state = await agent.navigate("https://example.com")
        await agent.click("button#submit")
        await agent.fill("#email", "user@example.com")
        data = await agent.extract_tables()
        await agent.stop()
    """

    def __init__(
        self,
        config: BrowserConfig | None = None,
        vision_analyzer: Any | None = None,
    ) -> None:
        self._config = config or BrowserConfig()
        self._analyzer = PageAnalyzer()
        self._session_mgr = SessionManager(storage_dir=self._config.cookie_dir or "")
        self._vision: Any | None = vision_analyzer
        self._playwright: Any = None
        self._browser: Any = None
        self._context: Any = None
        self._pages: list[Any] = []
        self._active_page_idx: int = 0
        self._running = False
        self._start_time: float = 0
        self._action_count = 0
        self._error_count = 0
        self._workflows: dict[str, BrowserWorkflow] = {}
        self._page_states: dict[str, PageState] = {}
        self._console_messages: list[str] = []

    @property
    def is_available(self) -> bool:
        return _HAS_PLAYWRIGHT

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def page(self) -> Any:
        """Active page."""
        if self._pages and 0 <= self._active_page_idx < len(self._pages):
            return self._pages[self._active_page_idx]
        return None

    @property
    def page_count(self) -> int:
        return len(self._pages)

    # ── Lifecycle ────────────────────────────────────────────────

    async def start(self, session_id: str = "") -> bool:
        """Starts browser instance."""
        if not _HAS_PLAYWRIGHT:
            log.warning("browser_playwright_not_installed")
            return False

        if self._running:
            return True

        try:
            self._playwright = await async_playwright().start()
            launch_opts: dict[str, Any] = {
                "headless": self._config.headless,
            }
            if self._config.proxy:
                launch_opts["proxy"] = {"server": self._config.proxy}

            # Stealth: anti-bot-detection
            try:
                from cognithor.browser.captcha.stealth import (
                    STEALTH_ARGS,
                    STEALTH_JS,
                )

                launch_opts.setdefault("args", []).extend(STEALTH_ARGS)
                _stealth_available = True
            except ImportError:
                _stealth_available = False

            self._browser = await self._playwright.chromium.launch(**launch_opts)

            context_opts: dict[str, Any] = {
                "viewport": {
                    "width": self._config.viewport_width,
                    "height": self._config.viewport_height,
                },
                "locale": self._config.locale,
                "timezone_id": self._config.timezone,
            }
            if self._config.user_agent:
                context_opts["user_agent"] = self._config.user_agent

            self._context = await self._browser.new_context(**context_opts)

            # Inject stealth JS on every new page
            if _stealth_available:
                await self._context.add_init_script(STEALTH_JS)

            # Restore session
            if session_id and self._config.persist_cookies:
                await self._session_mgr.restore_to_context(self._context, session_id)

            # Collect console messages
            self._context.on(
                "console",
                lambda msg: self._console_messages.append(f"[{msg.type}] {msg.text}"[:200]),
            )

            # First page
            page = await self._context.new_page()
            self._pages.append(page)
            self._active_page_idx = 0

            self._running = True
            self._start_time = time.time()
            log.info("browser_agent_started", headless=self._config.headless)
            return True

        except Exception as exc:
            log.error("browser_start_failed", error=str(exc))
            await self._cleanup()
            return False

    async def stop(self, session_id: str = "") -> None:
        """Stops browser and saves session."""
        if not self._running:
            return

        # Save session
        if session_id and self._config.persist_cookies and self.page:
            try:
                await self._session_mgr.save_from_page(self.page, session_id)
            except Exception as exc:
                log.debug("session_save_error", error=str(exc))

        await self._cleanup()
        log.info("browser_agent_stopped", actions=self._action_count, errors=self._error_count)

    async def _cleanup(self) -> None:
        self._running = False
        with contextlib.suppress(Exception):
            if self._context:
                await self._context.close()
        with contextlib.suppress(Exception):
            if self._browser:
                await self._browser.close()
        with contextlib.suppress(Exception):
            if self._playwright:
                await self._playwright.stop()
        self._pages.clear()
        self._context = None
        self._browser = None
        self._playwright = None

    # ── Core Actions ─────────────────────────────────────────────

    async def navigate(
        self, url: str, *, wait_until: str = "domcontentloaded", auto_dismiss_cookies: bool = True
    ) -> PageState:
        """Navigates to URL and analyzes the page."""
        self._ensure_running()
        start = time.monotonic()

        try:
            response = await self.page.goto(
                url,
                wait_until=wait_until,
                timeout=self._config.timeout_ms,
            )
            status = response.status if response else 0
        except Exception as exc:
            return PageState(url=url, errors=[str(exc)])

        # Automatically dismiss cookie banner
        if auto_dismiss_cookies:
            await self._try_dismiss_cookies()

        state = await self._analyzer.analyze(self.page)
        state.status_code = status
        state.load_time_ms = int((time.monotonic() - start) * 1000)
        state.tab_index = self._active_page_idx
        state.tab_count = len(self._pages)
        self._page_states[url] = state
        self._action_count += 1
        return state

    async def click(self, selector: str, *, timeout: int = 0) -> ActionResult:
        """Clicks on an element."""
        self._ensure_running()
        start = time.monotonic()
        old_url = self.page.url

        try:
            await self.page.click(
                selector,
                timeout=timeout or self._config.timeout_ms,
            )
            await self.page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception as exc:
            self._error_count += 1
            return ActionResult(
                action_id="",
                success=False,
                error=str(exc),
                duration_ms=int((time.monotonic() - start) * 1000),
            )

        new_url = self.page.url
        self._action_count += 1
        return ActionResult(
            action_id="",
            success=True,
            page_changed=new_url != old_url,
            new_url=new_url,
            duration_ms=int((time.monotonic() - start) * 1000),
        )

    async def fill(self, selector: str, value: str, *, clear: bool = True) -> ActionResult:
        """Fills a form field."""
        self._ensure_running()
        start = time.monotonic()

        try:
            if clear:
                await self.page.fill(selector, "", timeout=self._config.timeout_ms)
            await self.page.fill(selector, value, timeout=self._config.timeout_ms)
        except Exception as exc:
            self._error_count += 1
            return ActionResult(
                action_id="",
                success=False,
                error=str(exc),
                duration_ms=int((time.monotonic() - start) * 1000),
            )

        self._action_count += 1
        return ActionResult(
            action_id="", success=True, duration_ms=int((time.monotonic() - start) * 1000)
        )

    async def select(self, selector: str, value: str) -> ActionResult:
        """Selects an option in a select element."""
        self._ensure_running()
        start = time.monotonic()

        try:
            await self.page.select_option(selector, value, timeout=self._config.timeout_ms)
        except Exception as exc:
            self._error_count += 1
            return ActionResult(
                action_id="",
                success=False,
                error=str(exc),
                duration_ms=int((time.monotonic() - start) * 1000),
            )

        self._action_count += 1
        return ActionResult(
            action_id="", success=True, duration_ms=int((time.monotonic() - start) * 1000)
        )

    async def hover(self, selector: str) -> ActionResult:
        """Hovers the mouse over an element."""
        self._ensure_running()
        start = time.monotonic()
        try:
            await self.page.hover(selector, timeout=self._config.timeout_ms)
            self._action_count += 1
            return ActionResult(
                action_id="", success=True, duration_ms=int((time.monotonic() - start) * 1000)
            )
        except Exception as exc:
            self._error_count += 1
            return ActionResult(
                action_id="",
                success=False,
                error=str(exc),
                duration_ms=int((time.monotonic() - start) * 1000),
            )

    async def press_key(self, key: str) -> ActionResult:
        """Presses a key (Enter, Tab, Escape, etc.)."""
        self._ensure_running()
        start = time.monotonic()
        try:
            await self.page.keyboard.press(key)
            self._action_count += 1
            return ActionResult(
                action_id="", success=True, duration_ms=int((time.monotonic() - start) * 1000)
            )
        except Exception as exc:
            self._error_count += 1
            return ActionResult(
                action_id="",
                success=False,
                error=str(exc),
                duration_ms=int((time.monotonic() - start) * 1000),
            )

    async def scroll(self, direction: str = "down", amount: int = 500) -> ActionResult:
        """Scrolls the page."""
        self._ensure_running()
        dy = amount if direction == "down" else -amount
        try:
            await self.page.mouse.wheel(0, dy)
            await asyncio.sleep(0.3)
            self._action_count += 1
            return ActionResult(action_id="", success=True)
        except Exception as exc:
            return ActionResult(action_id="", success=False, error=str(exc))

    async def wait_for(
        self, selector: str, *, timeout: int = 0, state: str = "visible"
    ) -> ActionResult:
        """Waits for an element."""
        self._ensure_running()
        start = time.monotonic()
        try:
            await self.page.wait_for_selector(
                selector,
                state=state,
                timeout=timeout or self._config.timeout_ms,
            )
            return ActionResult(
                action_id="", success=True, duration_ms=int((time.monotonic() - start) * 1000)
            )
        except Exception as exc:
            return ActionResult(
                action_id="",
                success=False,
                error=str(exc),
                duration_ms=int((time.monotonic() - start) * 1000),
            )

    async def execute_js(self, script: str) -> ActionResult:
        """Executes JavaScript on the page."""
        self._ensure_running()
        start = time.monotonic()
        try:
            result = await self.page.evaluate(script)
            self._action_count += 1
            return ActionResult(
                action_id="",
                success=True,
                data=result,
                duration_ms=int((time.monotonic() - start) * 1000),
            )
        except Exception as exc:
            self._error_count += 1
            return ActionResult(
                action_id="",
                success=False,
                error=str(exc),
                duration_ms=int((time.monotonic() - start) * 1000),
            )

    # ── Screenshots ──────────────────────────────────────────────

    async def screenshot(self, *, full_page: bool = False, path: str = "") -> ActionResult:
        """Takes screenshot (returns Base64)."""
        self._ensure_running()
        start = time.monotonic()
        try:
            opts: dict[str, Any] = {"full_page": full_page, "type": "png"}
            if path:
                opts["path"] = path

            raw = await self.page.screenshot(**opts)
            b64 = base64.b64encode(raw).decode("ascii")
            self._action_count += 1
            return ActionResult(
                action_id="",
                success=True,
                screenshot_b64=b64,
                duration_ms=int((time.monotonic() - start) * 1000),
            )
        except Exception as exc:
            return ActionResult(
                action_id="",
                success=False,
                error=str(exc),
                duration_ms=int((time.monotonic() - start) * 1000),
            )

    # ── Tab Management ───────────────────────────────────────────

    async def new_tab(self, url: str = "") -> ActionResult:
        """Opens a new tab."""
        self._ensure_running()
        if len(self._pages) >= self._config.max_pages:
            return ActionResult(
                action_id="", success=False, error=f"Max tabs ({self._config.max_pages}) reached"
            )

        try:
            page = await self._context.new_page()
            self._pages.append(page)
            self._active_page_idx = len(self._pages) - 1
            if url:
                await page.goto(url, timeout=self._config.timeout_ms)
            self._action_count += 1
            return ActionResult(
                action_id="", success=True, data={"tab_index": self._active_page_idx}
            )
        except Exception as exc:
            return ActionResult(action_id="", success=False, error=str(exc))

    async def close_tab(self, index: int = -1) -> ActionResult:
        """Closes a tab."""
        self._ensure_running()
        if len(self._pages) <= 1:
            return ActionResult(action_id="", success=False, error="Cannot close last tab")

        idx = index if index >= 0 else self._active_page_idx
        if idx < 0 or idx >= len(self._pages):
            return ActionResult(action_id="", success=False, error="Invalid tab index")

        try:
            page = self._pages.pop(idx)
            await page.close()
            self._active_page_idx = min(self._active_page_idx, len(self._pages) - 1)
            return ActionResult(action_id="", success=True)
        except Exception as exc:
            return ActionResult(action_id="", success=False, error=str(exc))

    def switch_tab(self, index: int) -> ActionResult:
        """Switches the active tab."""
        if 0 <= index < len(self._pages):
            self._active_page_idx = index
            return ActionResult(action_id="", success=True)
        return ActionResult(action_id="", success=False, error="Invalid tab index")

    # ── Content Extraction ───────────────────────────────────────

    async def analyze_page(self) -> PageState:
        """Analyzes the current page."""
        self._ensure_running()
        state = await self._analyzer.analyze(self.page)
        state.tab_index = self._active_page_idx
        state.tab_count = len(self._pages)
        state.console_messages = self._console_messages[-20:]
        return state

    async def extract_text(self, selector: str = "body") -> str:
        """Extracts text from an element."""
        self._ensure_running()
        try:
            # Use parameterized evaluate to prevent CSS selector injection
            return (
                await self.page.evaluate(
                    "(sel) => document.querySelector(sel)?.innerText || ''",
                    selector,
                )
                or ""
            )
        except Exception:
            return ""

    async def extract_tables(self) -> list[dict[str, Any]]:
        """Extracts all tables from the page."""
        self._ensure_running()
        state = await self._analyzer.analyze(self.page, extract_text=False)
        return state.tables

    async def extract_links(self) -> list[dict[str, str]]:
        """Extracts all links."""
        self._ensure_running()
        state = await self._analyzer.analyze(self.page, extract_text=False)
        return [{"text": link.text, "href": link.href} for link in state.links if link.href]

    async def find_and_click(self, description: str) -> ActionResult:
        """Finds an element by description and clicks on it."""
        self._ensure_running()
        element = await self._analyzer.find_element(self.page, description)
        if element is None:
            return ActionResult(
                action_id="", success=False, error=f"Element not found: {description}"
            )
        return await self.click(element.selector)

    # ── Form Automation ──────────────────────────────────────────

    async def fill_form(self, data: dict[str, str], *, submit: bool = False) -> list[ActionResult]:
        """Fills a form with the given data.

        Args:
            data: Mapping of field name/label to value
            submit: Submit the form after filling?
        """
        self._ensure_running()
        state = await self._analyzer.analyze(self.page, extract_text=False)
        results: list[ActionResult] = []

        for form in state.forms:
            for fld in form.fields:
                value = data.get(fld.name) or data.get(fld.label)
                if value is None:
                    continue

                if fld.field_type in ("select", "select-one"):
                    result = await self.select(fld.selector, value)
                else:
                    result = await self.fill(fld.selector, value)
                results.append(result)

            if submit and form.submit_selector:
                results.append(await self.click(form.submit_selector))
            break  # First form

        return results

    # ── Workflow Execution ───────────────────────────────────────

    async def execute_workflow(self, workflow: BrowserWorkflow) -> BrowserWorkflow:
        """Executes a multi-step workflow."""
        self._ensure_running()
        workflow.status = WorkflowStatus.RUNNING
        self._workflows[workflow.workflow_id] = workflow

        for i, step in enumerate(workflow.steps):
            if workflow.status != WorkflowStatus.RUNNING:
                break

            workflow.current_step = i
            result = await self._execute_action(step)
            workflow.results.append(result)

            if not result.success:
                # Retry
                retried = False
                for _attempt in range(workflow.max_retries):
                    await asyncio.sleep(1)
                    retry_result = await self._execute_action(step)
                    if retry_result.success:
                        workflow.results[-1] = retry_result
                        retried = True
                        break

                if not retried:
                    workflow.status = WorkflowStatus.FAILED
                    if self._config.screenshot_on_error:
                        import tempfile

                        error_path = (
                            Path(tempfile.gettempdir())
                            / f"workflow_{workflow.workflow_id}_error.png"
                        )
                        await self.screenshot(path=str(error_path))
                    break

        if workflow.status == WorkflowStatus.RUNNING:
            workflow.status = WorkflowStatus.COMPLETED

        return workflow

    async def _execute_action(self, action: BrowserAction) -> ActionResult:
        """Executes a single BrowserAction."""
        start = time.monotonic()
        params = action.params

        try:
            match action.action_type:
                case ActionType.NAVIGATE:
                    state = await self.navigate(params.get("url", ""))
                    return ActionResult(
                        action_id=action.action_id,
                        success=not state.errors,
                        data=state.to_dict(),
                        duration_ms=int((time.monotonic() - start) * 1000),
                    )
                case ActionType.CLICK:
                    return await self.click(params.get("selector", ""))
                case ActionType.FILL:
                    return await self.fill(params.get("selector", ""), params.get("value", ""))
                case ActionType.SELECT:
                    return await self.select(params.get("selector", ""), params.get("value", ""))
                case ActionType.SCROLL:
                    return await self.scroll(
                        params.get("direction", "down"), params.get("amount", 500)
                    )
                case ActionType.SCREENSHOT:
                    return await self.screenshot(full_page=params.get("full_page", False))
                case ActionType.WAIT:
                    await asyncio.sleep(params.get("seconds", 1))
                    return ActionResult(action_id=action.action_id, success=True)
                case ActionType.WAIT_FOR:
                    return await self.wait_for(params.get("selector", ""))
                case ActionType.EXECUTE_JS:
                    return await self.execute_js(params.get("script", ""))
                case ActionType.GO_BACK:
                    await self.page.go_back(timeout=self._config.timeout_ms)
                    return ActionResult(action_id=action.action_id, success=True)
                case ActionType.GO_FORWARD:
                    await self.page.go_forward(timeout=self._config.timeout_ms)
                    return ActionResult(action_id=action.action_id, success=True)
                case ActionType.REFRESH:
                    await self.page.reload(timeout=self._config.timeout_ms)
                    return ActionResult(action_id=action.action_id, success=True)
                case ActionType.NEW_TAB:
                    return await self.new_tab(params.get("url", ""))
                case ActionType.CLOSE_TAB:
                    return await self.close_tab(params.get("index", -1))
                case ActionType.SWITCH_TAB:
                    return self.switch_tab(params.get("index", 0))
                case ActionType.HOVER:
                    return await self.hover(params.get("selector", ""))
                case ActionType.PRESS_KEY:
                    return await self.press_key(params.get("key", "Enter"))
                case ActionType.EXTRACT_TEXT:
                    text = await self.extract_text(params.get("selector", "body"))
                    return ActionResult(action_id=action.action_id, success=True, data=text)
                case ActionType.EXTRACT_TABLE:
                    tables = await self.extract_tables()
                    return ActionResult(action_id=action.action_id, success=True, data=tables)
                case ActionType.EXTRACT_LINKS:
                    links = await self.extract_links()
                    return ActionResult(action_id=action.action_id, success=True, data=links)
                case _:
                    return ActionResult(
                        action_id=action.action_id,
                        success=False,
                        error=f"Unknown action: {action.action_type}",
                    )
        except Exception as exc:
            self._error_count += 1
            return ActionResult(
                action_id=action.action_id,
                success=False,
                error=str(exc),
                duration_ms=int((time.monotonic() - start) * 1000),
            )

    # ── Cookie Banner ────────────────────────────────────────────

    async def _try_dismiss_cookies(self) -> bool:
        """Attempts to automatically dismiss cookie banner."""
        try:
            banner = await self._analyzer.detect_cookie_banner(self.page)
            if banner.get("found") and banner.get("acceptSelector"):
                await self.page.click(banner["acceptSelector"], timeout=3000)
                await asyncio.sleep(0.5)
                log.debug("cookie_banner_dismissed", selector=banner["acceptSelector"])
                return True
        except Exception:
            pass  # Cleanup — cookie banner dismissal failure is non-critical
        return False

    # ── Vision-Integration ──────────────────────────────────────

    async def _extract_page_content(self, max_chars: int = 15_000) -> str:
        """Extracts cleaned HTML (without script/style/noscript/svg)."""
        try:
            js = """(() => {
                const c = document.body.cloneNode(true);
                c.querySelectorAll('script,style,noscript,svg,link[rel=stylesheet]').forEach(e=>e.remove());
                return c.innerHTML;
            })()"""
            raw = await self.page.evaluate(js)
            return (raw or "")[:max_chars]
        except Exception as exc:
            log.debug("page_content_extraction_error", error=str(exc))
            return ""

    async def analyze_page_with_vision(self, prompt: str = "") -> dict[str, Any]:
        """Analyzes the current page with DOM + optional Vision LLM.

        Args:
            prompt: Optional custom prompt for the vision analysis.

        Returns:
            Dict with "dom" (PageState summary), "vision" (str) and "combined" (str).
        """
        self._ensure_running()

        # DOM analysis (always available)
        state = await self.analyze_page()
        dom_summary = state.to_summary(max_text=2000)

        # Vision analysis (optional)
        vision_text = ""
        if self._vision is not None and getattr(self._vision, "is_enabled", False):
            try:
                result = await self.screenshot()
                if result.success and result.screenshot_b64:
                    page_content = await self._extract_page_content()
                    vision_result = await self._vision.analyze_screenshot(
                        result.screenshot_b64, prompt, page_content=page_content
                    )
                    if vision_result.success:
                        vision_text = vision_result.description
            except Exception as exc:
                log.debug("vision_analysis_error", error=str(exc))

        combined = dom_summary
        if vision_text:
            combined = f"## DOM-Analyse\n{dom_summary}\n\n## Vision-Analyse\n{vision_text}"

        return {
            "dom": dom_summary,
            "vision": vision_text,
            "combined": combined,
        }

    async def find_and_click_with_vision(self, description: str) -> ActionResult:
        """Finds and clicks an element by text match, with vision fallback.

        Args:
            description: Description of the element to find.

        Returns:
            ActionResult -- with vision fallback, data["vision_hint"] contains the hint.
        """
        self._ensure_running()

        # Text-based fuzzy matching first (fast)
        result = await self.find_and_click(description)
        if result.success:
            return result

        # Vision fallback when text match fails
        if self._vision is not None and getattr(self._vision, "is_enabled", False):
            try:
                ss_result = await self.screenshot()
                if ss_result.success and ss_result.screenshot_b64:
                    page_content = await self._extract_page_content()
                    vision_result = await self._vision.find_element_by_vision(
                        ss_result.screenshot_b64, description, page_content=page_content
                    )
                    if vision_result.success:
                        result.data["vision_hint"] = vision_result.description
            except Exception as exc:
                log.debug("vision_find_error", error=str(exc))

        return result

    # ── Helpers ───────────────────────────────────────────────────

    def _ensure_running(self) -> None:
        if not self._running:
            raise RuntimeError("BrowserAgent not started. Call start() first.")

    def get_workflow(self, workflow_id: str) -> BrowserWorkflow | None:
        return self._workflows.get(workflow_id)

    def stats(self) -> dict[str, Any]:
        uptime = time.time() - self._start_time if self._start_time else 0
        result = {
            "available": _HAS_PLAYWRIGHT,
            "running": self._running,
            "headless": self._config.headless,
            "uptime_seconds": round(uptime, 1),
            "total_actions": self._action_count,
            "total_errors": self._error_count,
            "tab_count": len(self._pages),
            "active_tab": self._active_page_idx,
            "workflows": len(self._workflows),
            "sessions": self._session_mgr.stats(),
            "analyzer": self._analyzer.stats(),
        }
        if self._vision is not None:
            result["vision"] = self._vision.stats()
        return result
