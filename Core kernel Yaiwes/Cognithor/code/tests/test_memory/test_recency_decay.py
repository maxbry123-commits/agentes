"""Tests for recency_decay() half-life correctness. [B§4.7]

Validates the fix from exp(-age/half_life) → 2^(-age/half_life),
ensuring true half-life semantics: the decay factor is exactly 0.5
after half_life_days.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from unittest.mock import patch

import pytest

from cognithor.memory.search import recency_decay

# Fixed "today" so tests are deterministic regardless of when they run.
FIXED_TODAY = date(2026, 3, 5)


@pytest.fixture(autouse=True)
def _freeze_today():
    """Patch date.today() to return a fixed date for all tests."""
    with patch("cognithor.memory.search.date") as mock_date:
        mock_date.today.return_value = FIXED_TODAY
        # Keep side_effect-free so date(...) constructor still works
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
        yield


def _days_ago(n: int) -> date:
    """Return a date that is *n* days before FIXED_TODAY."""
    return FIXED_TODAY - timedelta(days=n)


# ── Core half-life properties ────────────────────────────────────


def test_zero_age_returns_one():
    """A memory from today should have a decay of exactly 1.0."""
    assert recency_decay(_days_ago(0)) == 1.0


def test_half_life_returns_half():
    """After exactly one half-life (30 days) the decay must be 0.5."""
    assert recency_decay(_days_ago(30), half_life_days=30) == pytest.approx(0.5, abs=1e-12)


def test_double_half_life_returns_quarter():
    """After two half-lives (60 days) the decay must be 0.25."""
    assert recency_decay(_days_ago(60), half_life_days=30) == pytest.approx(0.25, abs=1e-12)


def test_triple_half_life():
    """After three half-lives (90 days) the decay must be 0.125."""
    assert recency_decay(_days_ago(90), half_life_days=30) == pytest.approx(0.125, abs=1e-12)


# ── Edge cases ───────────────────────────────────────────────────


def test_none_date_returns_one():
    """Entries without a date (None) always get full weight."""
    assert recency_decay(None) == 1.0


def test_future_date_returns_one():
    """A date in the future should clamp to 1.0 (no negative decay)."""
    future = FIXED_TODAY + timedelta(days=5)
    assert recency_decay(future) == 1.0


# ── Custom half-life ─────────────────────────────────────────────


def test_custom_half_life():
    """With a 7-day half-life, decay at 7 days must be exactly 0.5."""
    assert recency_decay(_days_ago(7), half_life_days=7) == pytest.approx(0.5, abs=1e-12)


def test_custom_half_life_double():
    """With a 7-day half-life, decay at 14 days must be exactly 0.25."""
    assert recency_decay(_days_ago(14), half_life_days=7) == pytest.approx(0.25, abs=1e-12)


# ── Datetime input ───────────────────────────────────────────────


def test_yesterday():
    """One day old should be close to 1.0 but strictly less than 1.0."""
    result = recency_decay(_days_ago(1), half_life_days=30)
    assert 0.97 < result < 1.0


def test_datetime_input():
    """datetime objects (not just date) should work identically."""
    dt = datetime.combine(_days_ago(30), datetime.min.time())
    assert recency_decay(dt, half_life_days=30) == pytest.approx(0.5, abs=1e-12)
