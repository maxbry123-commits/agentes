"""Tests for browser stealth configuration."""

from __future__ import annotations

from cognithor.browser.captcha.stealth import (
    DEFAULT_VIEWPORT,
    REALISTIC_USER_AGENT,
    STEALTH_ARGS,
    STEALTH_JS,
    get_stealth_context_opts,
    get_stealth_launch_opts,
)


def test_stealth_args_disables_automation():
    assert any("AutomationControlled" in a for a in STEALTH_ARGS)


def test_stealth_js_hides_webdriver():
    assert "webdriver" in STEALTH_JS
    assert "false" in STEALTH_JS


def test_realistic_user_agent():
    assert "Chrome/" in REALISTIC_USER_AGENT
    assert "Windows NT" in REALISTIC_USER_AGENT


def test_default_viewport():
    assert DEFAULT_VIEWPORT["width"] == 1280
    assert DEFAULT_VIEWPORT["height"] == 720


def test_get_stealth_launch_opts():
    opts = get_stealth_launch_opts(headless=True)
    assert opts["headless"] is True
    assert "args" in opts
    assert any("AutomationControlled" in a for a in opts["args"])


def test_get_stealth_context_opts():
    opts = get_stealth_context_opts()
    assert "user_agent" in opts
    assert "viewport" in opts
    assert opts["viewport"]["width"] == 1280


def test_stealth_disabled():
    opts = get_stealth_launch_opts(headless=True, stealth=False)
    assert "args" not in opts
