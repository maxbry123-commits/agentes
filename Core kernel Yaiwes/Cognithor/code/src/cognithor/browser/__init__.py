"""Cognithor Browser-Use v17 -- Autonomous browser automation.

Enables the agent to autonomously navigate, read and interact with
web pages. Headless Chromium via Playwright.

OPTIONAL: pip install playwright && playwright install chromium

Core components:
  - BrowserAgent:     Autonomous browser controller
  - PageAnalyzer:     Page analysis (forms, links, tables)
  - SessionManager:   Cookie/state persistence
  - register_browser_use_tools(): MCP tool integration
"""

from cognithor.browser.agent import BrowserAgent
from cognithor.browser.page_analyzer import PageAnalyzer
from cognithor.browser.session_manager import SessionManager, SessionSnapshot
from cognithor.browser.tools import register_browser_use_tools
from cognithor.browser.types import (
    ActionResult,
    ActionType,
    BrowserAction,
    BrowserConfig,
    BrowserWorkflow,
    ElementInfo,
    ElementType,
    ExtractionMode,
    FormField,
    FormInfo,
    PageState,
    WorkflowStatus,
)

__all__ = [
    "ActionResult",
    "ActionType",
    "BrowserAction",
    "BrowserAgent",
    "BrowserConfig",
    "BrowserWorkflow",
    "ElementInfo",
    "ElementType",
    "ExtractionMode",
    "FormField",
    "FormInfo",
    "PageAnalyzer",
    "PageState",
    "SessionManager",
    "SessionSnapshot",
    "WorkflowStatus",
    "register_browser_use_tools",
]
