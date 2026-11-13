"""Tests for CAPTCHA solver orchestrator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cognithor.browser.captcha.models import CaptchaType, SolveResult
from cognithor.browser.captcha.solver import CaptchaConfig, CaptchaSolver


@pytest.fixture
def solver():
    return CaptchaSolver(
        vision_fn=AsyncMock(return_value="abc123"),
        config=CaptchaConfig(enabled=True),
    )


@pytest.fixture
def mock_page():
    page = MagicMock()
    page.evaluate = AsyncMock(return_value=[])
    page.url = "https://example.com"
    return page


@pytest.mark.asyncio
async def test_solve_no_captcha(solver, mock_page):
    result = await solver.solve(mock_page)
    assert result.success is True
    assert "No CAPTCHA" in result.answer


@pytest.mark.asyncio
async def test_solve_with_detected_challenge(solver, mock_page):
    mock_page.evaluate = AsyncMock(
        return_value=[
            {"type": "text", "selector": "img.captcha", "sitekey": ""},
        ]
    )
    with patch("cognithor.browser.captcha.solver.get_strategy") as mock_gs:

        async def fake_strat(page, challenge, vision_fn):
            return SolveResult(
                success=True,
                captcha_type=CaptchaType.TEXT,
                model_used="test",
                attempts=1,
                duration_ms=100,
                answer="ok",
            )

        mock_gs.return_value = fake_strat
        result = await solver.solve(mock_page)
        assert result.success


@pytest.mark.asyncio
async def test_solve_retry_on_failure(solver, mock_page):
    mock_page.evaluate = AsyncMock(
        return_value=[
            {"type": "text", "selector": "img.captcha", "sitekey": ""},
        ]
    )
    call_count = 0
    with patch("cognithor.browser.captcha.solver.get_strategy") as mock_gs:

        async def failing_then_ok(page, challenge, vision_fn):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return SolveResult(
                    success=False,
                    captcha_type=CaptchaType.TEXT,
                    model_used="test",
                    attempts=call_count,
                    duration_ms=50,
                    error="wrong",
                )
            return SolveResult(
                success=True,
                captcha_type=CaptchaType.TEXT,
                model_used="test",
                attempts=call_count,
                duration_ms=150,
                answer="ok",
            )

        mock_gs.return_value = failing_then_ok
        result = await solver.solve(mock_page)
        assert result.success
        assert call_count == 3


@pytest.mark.asyncio
async def test_solve_all_retries_exhausted(solver, mock_page):
    mock_page.evaluate = AsyncMock(
        return_value=[
            {"type": "text", "selector": "img.captcha", "sitekey": ""},
        ]
    )
    with patch("cognithor.browser.captcha.solver.get_strategy") as mock_gs:

        async def always_fail(page, challenge, vision_fn):
            return SolveResult(
                success=False,
                captcha_type=CaptchaType.TEXT,
                model_used="test",
                attempts=1,
                duration_ms=50,
                error="nope",
            )

        mock_gs.return_value = always_fail
        result = await solver.solve(mock_page)
        assert not result.success
        assert result.attempts == 3


def test_captcha_config_defaults():
    cfg = CaptchaConfig()
    assert cfg.enabled is False
    assert cfg.max_retries == 3
    assert cfg.stealth_enabled is True
    assert cfg.auto_solve is True
    assert cfg.solve_timeout_seconds == 30
