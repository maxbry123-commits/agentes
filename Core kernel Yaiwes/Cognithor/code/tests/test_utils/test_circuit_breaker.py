"""Tests für CircuitBreaker — Schutz gegen kaskadierende Fehler."""

from __future__ import annotations

import asyncio

import pytest

from cognithor.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpen,
    CircuitState,
)

# ============================================================================
# Hilfsfunktionen
# ============================================================================


async def _succeed() -> str:
    return "ok"


async def _fail() -> str:
    raise RuntimeError("boom")


async def _fail_value() -> str:
    raise ValueError("bad input")


# ============================================================================
# State-Tests
# ============================================================================


class TestStates:
    @pytest.mark.asyncio
    async def test_starts_closed(self) -> None:
        cb = CircuitBreaker(name="test")
        assert cb.state == CircuitState.closed

    @pytest.mark.asyncio
    async def test_success_stays_closed(self) -> None:
        cb = CircuitBreaker(name="test", failure_threshold=3)
        result = await cb.call(_succeed())
        assert result == "ok"
        assert cb.state == CircuitState.closed

    @pytest.mark.asyncio
    async def test_below_threshold_stays_closed(self) -> None:
        cb = CircuitBreaker(name="test", failure_threshold=3)
        for _ in range(2):
            with pytest.raises(RuntimeError):
                await cb.call(_fail())
        assert cb.state == CircuitState.closed

    @pytest.mark.asyncio
    async def test_at_threshold_opens(self) -> None:
        cb = CircuitBreaker(name="test", failure_threshold=3)
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await cb.call(_fail())
        assert cb.state == CircuitState.open

    @pytest.mark.asyncio
    async def test_open_rejects(self) -> None:
        cb = CircuitBreaker(name="test", failure_threshold=2, recovery_timeout=60.0)
        for _ in range(2):
            with pytest.raises(RuntimeError):
                await cb.call(_fail())

        with pytest.raises(CircuitBreakerOpen) as exc_info:
            await cb.call(_succeed())
        assert exc_info.value.name == "test"
        assert exc_info.value.remaining_seconds > 0

    @pytest.mark.asyncio
    async def test_open_to_half_open_after_timeout(self) -> None:
        cb = CircuitBreaker(name="test", failure_threshold=2, recovery_timeout=0.1)
        for _ in range(2):
            with pytest.raises(RuntimeError):
                await cb.call(_fail())
        assert cb.state == CircuitState.open

        await asyncio.sleep(0.15)

        # Nächster Call sollte HALF_OPEN triggern und durchgehen
        result = await cb.call(_succeed())
        assert result == "ok"
        assert cb.state == CircuitState.closed  # half_open_max_calls=1 default

    @pytest.mark.asyncio
    async def test_half_open_success_closes(self) -> None:
        cb = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.1,
            half_open_max_calls=1,
        )
        for _ in range(2):
            with pytest.raises(RuntimeError):
                await cb.call(_fail())

        await asyncio.sleep(0.15)

        await cb.call(_succeed())
        assert cb.state == CircuitState.closed
        assert cb._failure_count == 0

    @pytest.mark.asyncio
    async def test_half_open_failure_reopens(self) -> None:
        cb = CircuitBreaker(name="test", failure_threshold=2, recovery_timeout=0.1)
        for _ in range(2):
            with pytest.raises(RuntimeError):
                await cb.call(_fail())

        await asyncio.sleep(0.15)

        # Fehler in HALF_OPEN → zurück zu OPEN
        with pytest.raises(RuntimeError):
            await cb.call(_fail())
        assert cb.state == CircuitState.open

    @pytest.mark.asyncio
    async def test_success_resets_failure_count(self) -> None:
        cb = CircuitBreaker(name="test", failure_threshold=3)
        with pytest.raises(RuntimeError):
            await cb.call(_fail())
        with pytest.raises(RuntimeError):
            await cb.call(_fail())

        # Erfolg setzt Zähler zurück
        await cb.call(_succeed())
        assert cb._failure_count == 0

        # Braucht jetzt wieder 3 Fehler
        with pytest.raises(RuntimeError):
            await cb.call(_fail())
        assert cb.state == CircuitState.closed


# ============================================================================
# Excluded Exceptions
# ============================================================================


class TestExclusions:
    @pytest.mark.asyncio
    async def test_excluded_exceptions_not_counted(self) -> None:
        cb = CircuitBreaker(
            name="test",
            failure_threshold=2,
            excluded_exceptions=(ValueError,),
        )
        for _ in range(5):
            with pytest.raises(ValueError):
                await cb.call(_fail_value())

        # Circuit sollte immer noch CLOSED sein
        assert cb.state == CircuitState.closed
        assert cb._failure_count == 0


# ============================================================================
# Metrics
# ============================================================================


class TestMetrics:
    @pytest.mark.asyncio
    async def test_stats_reporting(self) -> None:
        cb = CircuitBreaker(name="metrics_test", failure_threshold=3)
        await cb.call(_succeed())
        with pytest.raises(RuntimeError):
            await cb.call(_fail())

        stats = cb.stats
        assert stats["name"] == "metrics_test"
        assert stats["state"] == "closed"
        assert stats["total_calls"] == 2
        assert stats["total_failures"] == 1

    @pytest.mark.asyncio
    async def test_rejections_counted(self) -> None:
        cb = CircuitBreaker(name="test", failure_threshold=2, recovery_timeout=60.0)
        for _ in range(2):
            with pytest.raises(RuntimeError):
                await cb.call(_fail())

        with pytest.raises(CircuitBreakerOpen):
            await cb.call(_succeed())

        assert cb.stats["total_rejections"] == 1

    @pytest.mark.asyncio
    async def test_state_changes_counted(self) -> None:
        cb = CircuitBreaker(name="test", failure_threshold=2, recovery_timeout=0.1)
        for _ in range(2):
            with pytest.raises(RuntimeError):
                await cb.call(_fail())
        # closed → open = 1 change
        assert cb.stats["state_changes"] == 1

        await asyncio.sleep(0.15)
        await cb.call(_succeed())
        # open → half_open → closed = 2 more changes
        assert cb.stats["state_changes"] == 3


# ============================================================================
# Reset
# ============================================================================


class TestReset:
    @pytest.mark.asyncio
    async def test_manual_reset(self) -> None:
        cb = CircuitBreaker(name="test", failure_threshold=2)
        for _ in range(2):
            with pytest.raises(RuntimeError):
                await cb.call(_fail())
        assert cb.state == CircuitState.open

        cb.reset()
        assert cb.state == CircuitState.closed
        assert cb._failure_count == 0

        # Sollte wieder funktionieren
        result = await cb.call(_succeed())
        assert result == "ok"


# ============================================================================
# Concurrency
# ============================================================================


class TestConcurrency:
    @pytest.mark.asyncio
    async def test_concurrent_calls(self) -> None:
        cb = CircuitBreaker(name="test", failure_threshold=5)

        async def delayed_succeed() -> str:
            await asyncio.sleep(0.01)
            return "ok"

        results = await asyncio.gather(*[cb.call(delayed_succeed()) for _ in range(10)])
        assert all(r == "ok" for r in results)
        assert cb.stats["total_calls"] == 10
