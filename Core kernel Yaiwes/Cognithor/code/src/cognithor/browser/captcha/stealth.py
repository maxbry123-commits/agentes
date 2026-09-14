"""Browser stealth — anti-bot-detection basics for Playwright."""

from __future__ import annotations

from typing import Any

__all__ = [
    "DEFAULT_VIEWPORT",
    "REALISTIC_USER_AGENT",
    "STEALTH_ARGS",
    "STEALTH_JS",
    "get_stealth_context_opts",
    "get_stealth_launch_opts",
]

STEALTH_ARGS: list[str] = [
    "--disable-blink-features=AutomationControlled",
    "--disable-features=IsolateOrigins,site-per-process",
    "--disable-dev-shm-usage",
]

STEALTH_JS = """\
Object.defineProperty(navigator, 'webdriver', {get: () => false});
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5],
});
Object.defineProperty(navigator, 'languages', {
    get: () => ['de-DE', 'de', 'en-US', 'en'],
});
if (!window.chrome) window.chrome = {runtime: {}};
"""

REALISTIC_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

DEFAULT_VIEWPORT = {"width": 1280, "height": 720}


def get_stealth_launch_opts(
    *,
    headless: bool = True,
    stealth: bool = True,
) -> dict[str, Any]:
    opts: dict[str, Any] = {"headless": headless}
    if stealth:
        opts["args"] = list(STEALTH_ARGS)
    return opts


def get_stealth_context_opts(*, stealth: bool = True) -> dict[str, Any]:
    opts: dict[str, Any] = {
        "viewport": dict(DEFAULT_VIEWPORT),
        "locale": "de-DE",
        "timezone_id": "Europe/Berlin",
    }
    if stealth:
        opts["user_agent"] = REALISTIC_USER_AGENT
    return opts
