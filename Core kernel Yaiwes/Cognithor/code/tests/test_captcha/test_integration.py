"""Integration tests for CAPTCHA solver."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from cognithor.browser.captcha.models import CaptchaType
from cognithor.browser.captcha.solver import CaptchaConfig, CaptchaSolver
from cognithor.browser.captcha.stealth import STEALTH_ARGS, STEALTH_JS


@pytest.mark.asyncio
async def test_full_flow_no_captcha():
    page = MagicMock()
    page.evaluate = AsyncMock(return_value=[])
    page.url = "https://example.com"
    solver = CaptchaSolver(
        vision_fn=AsyncMock(return_value=""),
        config=CaptchaConfig(enabled=True),
    )
    result = await solver.solve(page)
    assert result.success


@pytest.mark.asyncio
async def test_full_flow_text_captcha():
    page = MagicMock()
    page.evaluate = AsyncMock(
        return_value=[
            {"type": "text", "selector": "img.captcha", "sitekey": ""},
        ]
    )
    page.url = "https://example.com"
    page.query_selector = AsyncMock(
        return_value=MagicMock(
            screenshot=AsyncMock(return_value=b"fake-png"),
        )
    )
    page.fill = AsyncMock()
    solver = CaptchaSolver(
        vision_fn=AsyncMock(return_value="XY42Z"),
        config=CaptchaConfig(enabled=True),
    )
    result = await solver.solve(page)
    assert isinstance(result.captcha_type, CaptchaType)


def test_stealth_constants():
    assert len(STEALTH_ARGS) >= 1
    assert "webdriver" in STEALTH_JS
