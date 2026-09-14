"""Tests for CAPTCHA solve strategies."""

from __future__ import annotations

from cognithor.browser.captcha.models import CaptchaType
from cognithor.browser.captcha.strategies import (
    build_image_grid_prompt,
    build_text_captcha_prompt,
    get_strategy,
    parse_grid_coordinates,
    parse_text_answer,
)


def test_build_text_prompt():
    prompt = build_text_captcha_prompt()
    assert "verzerrten Text" in prompt or "CAPTCHA" in prompt


def test_build_image_grid_prompt():
    prompt = build_image_grid_prompt("Select all images with traffic lights")
    assert "traffic lights" in prompt


def test_parse_text_answer_clean():
    assert parse_text_answer("abc123") == "abc123"


def test_parse_text_answer_strips_quotes():
    assert parse_text_answer('"abc123"') == "abc123"


def test_parse_text_answer_strips_explanation():
    result = parse_text_answer("The text reads: abc123")
    assert "abc123" in result


def test_parse_text_answer_strips_german():
    result = parse_text_answer("Der Text lautet: XY42Z")
    assert "XY42Z" in result


def test_parse_grid_coordinates_valid():
    coords = parse_grid_coordinates("[[0,1],[1,2],[2,0]]")
    assert coords == [(0, 1), (1, 2), (2, 0)]


def test_parse_grid_coordinates_from_text():
    coords = parse_grid_coordinates("The matching images are at positions [0,2] and [1,1]")
    assert (0, 2) in coords
    assert (1, 1) in coords


def test_parse_grid_coordinates_empty():
    coords = parse_grid_coordinates("I cannot identify any matching images")
    assert coords == []


def test_get_strategy_returns_callable():
    for ct in [
        CaptchaType.TEXT,
        CaptchaType.RECAPTCHA_V2_CHECKBOX,
        CaptchaType.RECAPTCHA_V2_IMAGE,
        CaptchaType.HCAPTCHA,
        CaptchaType.TURNSTILE,
        CaptchaType.FUNCAPTCHA,
    ]:
        s = get_strategy(ct)
        assert s is not None
        assert callable(s)


def test_get_strategy_unknown_returns_generic():
    s = get_strategy(CaptchaType.UNKNOWN)
    assert s is not None
    assert callable(s)
