"""Tests for CAPTCHA classifier."""

from __future__ import annotations

from cognithor.browser.captcha.classifier import classify_challenge, select_vision_model
from cognithor.browser.captcha.models import CaptchaChallenge, CaptchaType


def test_classify_text():
    c = CaptchaChallenge(captcha_type=CaptchaType.TEXT, selector="img.captcha")
    result = classify_challenge(c)
    assert result.needs_vision is True
    assert result.needs_click is False
    assert result.complexity == "simple"


def test_classify_recaptcha_v2_checkbox():
    c = CaptchaChallenge(captcha_type=CaptchaType.RECAPTCHA_V2_CHECKBOX, selector=".g-recaptcha")
    result = classify_challenge(c)
    assert result.needs_click is True
    assert result.may_escalate is True


def test_classify_recaptcha_v2_image():
    c = CaptchaChallenge(captcha_type=CaptchaType.RECAPTCHA_V2_IMAGE, selector=".g-recaptcha")
    result = classify_challenge(c)
    assert result.needs_vision is True
    assert result.complexity == "complex"


def test_classify_recaptcha_v3():
    c = CaptchaChallenge(captcha_type=CaptchaType.RECAPTCHA_V3, selector="")
    result = classify_challenge(c)
    assert result.needs_vision is False
    assert result.needs_stealth is True


def test_select_model_simple():
    model = select_vision_model(CaptchaType.TEXT)
    assert "minicpm" in model


def test_select_model_complex():
    model = select_vision_model(CaptchaType.RECAPTCHA_V2_IMAGE)
    assert "qwen3-vl" in model


def test_select_model_no_vision():
    model = select_vision_model(CaptchaType.RECAPTCHA_V3)
    assert model == ""
