"""Tests for CAPTCHA detector."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from cognithor.browser.captcha.detector import DETECT_JS, detect_captcha
from cognithor.browser.captcha.models import CaptchaType


def _mock_page(js_result: list[dict]) -> MagicMock:
    page = MagicMock()
    page.evaluate = AsyncMock(return_value=js_result)
    page.url = "https://example.com/login"
    return page


@pytest.mark.asyncio
async def test_detect_recaptcha_v2():
    page = _mock_page([{"type": "recaptcha_v2", "selector": ".g-recaptcha", "sitekey": "6Le-ABC"}])
    challenges = await detect_captcha(page)
    assert len(challenges) == 1
    assert challenges[0].captcha_type == CaptchaType.RECAPTCHA_V2_CHECKBOX
    assert challenges[0].sitekey == "6Le-ABC"


@pytest.mark.asyncio
async def test_detect_hcaptcha():
    page = _mock_page([{"type": "hcaptcha", "selector": ".h-captcha", "sitekey": "abc-123"}])
    challenges = await detect_captcha(page)
    assert len(challenges) == 1
    assert challenges[0].captcha_type == CaptchaType.HCAPTCHA


@pytest.mark.asyncio
async def test_detect_turnstile():
    page = _mock_page([{"type": "turnstile", "selector": ".cf-turnstile", "sitekey": "0x4AAA"}])
    challenges = await detect_captcha(page)
    assert len(challenges) == 1
    assert challenges[0].captcha_type == CaptchaType.TURNSTILE


@pytest.mark.asyncio
async def test_detect_text_captcha():
    page = _mock_page([{"type": "text", "selector": "img.captcha-image", "sitekey": ""}])
    challenges = await detect_captcha(page)
    assert len(challenges) == 1
    assert challenges[0].captcha_type == CaptchaType.TEXT


@pytest.mark.asyncio
async def test_detect_none():
    page = _mock_page([])
    challenges = await detect_captcha(page)
    assert len(challenges) == 0


@pytest.mark.asyncio
async def test_detect_multiple():
    page = _mock_page(
        [
            {"type": "recaptcha_v2", "selector": ".g-recaptcha", "sitekey": "abc"},
            {"type": "hcaptcha", "selector": ".h-captcha", "sitekey": "def"},
        ]
    )
    challenges = await detect_captcha(page)
    assert len(challenges) == 2


@pytest.mark.asyncio
async def test_detect_js_error_returns_empty():
    page = MagicMock()
    page.evaluate = AsyncMock(side_effect=Exception("JS error"))
    page.url = "https://example.com"
    challenges = await detect_captcha(page)
    assert len(challenges) == 0


def test_detect_js_contains_selectors():
    assert "g-recaptcha" in DETECT_JS
    assert "h-captcha" in DETECT_JS
    assert "cf-turnstile" in DETECT_JS
    assert "FunCaptcha" in DETECT_JS
