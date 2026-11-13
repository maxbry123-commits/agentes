"""Tests for CAPTCHA data models."""

from __future__ import annotations

from cognithor.browser.captcha.models import CaptchaChallenge, CaptchaType, SolveResult


def test_captcha_type_values():
    assert CaptchaType.TEXT == "text"
    assert CaptchaType.RECAPTCHA_V2_CHECKBOX == "recaptcha_v2_checkbox"
    assert CaptchaType.RECAPTCHA_V2_IMAGE == "recaptcha_v2_image"
    assert CaptchaType.RECAPTCHA_V3 == "recaptcha_v3"
    assert CaptchaType.HCAPTCHA == "hcaptcha"
    assert CaptchaType.TURNSTILE == "turnstile"
    assert CaptchaType.FUNCAPTCHA == "funcaptcha"
    assert CaptchaType.UNKNOWN == "unknown"


def test_captcha_challenge_defaults():
    c = CaptchaChallenge(captcha_type=CaptchaType.TEXT, selector="img.captcha")
    assert c.sitekey == ""
    assert c.iframe_url == ""
    assert c.page_url == ""
    assert c.screenshot_b64 == ""


def test_solve_result_success():
    r = SolveResult(
        success=True,
        captcha_type=CaptchaType.TEXT,
        model_used="minicpm-v4.5",
        attempts=1,
        duration_ms=1200,
        answer="abc123",
    )
    assert r.success
    assert r.error == ""


def test_solve_result_failure():
    r = SolveResult(
        success=False,
        captcha_type=CaptchaType.RECAPTCHA_V2_IMAGE,
        model_used="qwen3-vl:32b",
        attempts=3,
        duration_ms=15000,
        error="Vision model could not identify images",
    )
    assert not r.success
    assert r.attempts == 3
