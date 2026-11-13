"""Tests für CircuitBreaker HALF_OPEN Admission Control.

Validiert:
- Nur half_open_max_calls Probe-Calls kommen in HALF_OPEN durch
- Überschüssige Calls werden mit CircuitBreakerOpen abgewiesen
- Nach Erfolg → CLOSED, alle Calls wieder erlaubt
- Nach Failure → OPEN, Calls werden abgewiesen
"""

from __future__ import annotations

import asyncio

import pytest

from cognithor.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpen,
    CircuitState,
)


async def _trip_to_open(cb: CircuitBreaker) -> None:
    """Bringt den CircuitBreaker in OPEN-Zustand."""
    for _ in range(cb._failure_threshold):
        with pytest.raises(RuntimeError):
            await cb.call(_failing_coro())


async def _failing_coro():
    raise RuntimeError("fail")


async def _slow_coro(delay: float = 0.2):
    await asyncio.sleep(delay)
    return "ok"


async def _success_coro():
    return "ok"


class TestHalfOpenAdmission:
    """Testet die HALF_OPEN Admission Control."""

    async def test_only_one_call_in_halfopen(self) -> None:
        """Bei half_open_max_calls=1 kommt nur 1 Call durch."""
        cb = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.01,
            half_open_max_calls=1,
        )

        # OPEN-Zustand erzwingen
        await _trip_to_open(cb)
        assert cb.state == CircuitState.open

        # Warten bis recovery_timeout abläuft → HALF_OPEN
        await asyncio.sleep(0.02)

        # Erster Call: sollte durchkommen (langsam, damit zweiter noch sieht HALF_OPEN)
        results = []
        errors = []

        async def probe_call():
            try:
                r = await cb.call(_slow_coro(0.1))
                results.append(r)
            except CircuitBreakerOpen:
                errors.append("rejected")

        # 3 parallele Calls starten
        await asyncio.gather(probe_call(), probe_call(), probe_call())

        # Genau 1 sollte durchgekommen sein, 2 abgewiesen
        assert len(results) == 1
        assert len(errors) == 2

    async def test_halfopen_success_transitions_to_closed(self) -> None:
        """Nach Erfolg in HALF_OPEN → CLOSED."""
        cb = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.01,
            half_open_max_calls=1,
        )

        await _trip_to_open(cb)
        await asyncio.sleep(0.02)

        # Erfolgreicher Probe-Call
        result = await cb.call(_success_coro())
        assert result == "ok"
        assert cb.state == CircuitState.closed

    async def test_halfopen_failure_transitions_to_open(self) -> None:
        """Nach Failure in HALF_OPEN → zurück zu OPEN."""
        cb = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.01,
            half_open_max_calls=1,
        )

        await _trip_to_open(cb)
        await asyncio.sleep(0.02)

        # Fehlschlagender Probe-Call
        with pytest.raises(RuntimeError):
            await cb.call(_failing_coro())

        assert cb.state == CircuitState.open

    async def test_multiple_probe_calls_allowed(self) -> None:
        """Bei half_open_max_calls=3 kommen 3 Calls durch."""
        cb = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.01,
            half_open_max_calls=3,
        )

        await _trip_to_open(cb)
        await asyncio.sleep(0.02)

        results = []
        errors = []

        async def probe_call():
            try:
                r = await cb.call(_slow_coro(0.1))
                results.append(r)
            except CircuitBreakerOpen:
                errors.append("rejected")

        # 5 parallele Calls
        await asyncio.gather(*[probe_call() for _ in range(5)])

        assert len(results) == 3
        assert len(errors) == 2

    async def test_after_closed_all_calls_pass(self) -> None:
        """Nach Transition zu CLOSED sind alle Calls wieder erlaubt."""
        cb = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.01,
            half_open_max_calls=1,
        )

        await _trip_to_open(cb)
        await asyncio.sleep(0.02)

        # Probe → CLOSED
        await cb.call(_success_coro())
        assert cb.state == CircuitState.closed

        # Viele Calls sollten jetzt alle durchkommen
        results = await asyncio.gather(*[cb.call(_success_coro()) for _ in range(10)])
        assert len(results) == 10

    async def test_inflight_decremented_on_excluded_exception(self) -> None:
        """Excluded exceptions decrementieren den inflight-Zähler."""

        async def _raise_value_error():
            raise ValueError("excluded")

        cb = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.01,
            half_open_max_calls=1,
            excluded_exceptions=(ValueError,),
        )

        await _trip_to_open(cb)
        await asyncio.sleep(0.02)

        # Excluded Exception → Zähler zurückgesetzt
        with pytest.raises(ValueError):
            await cb.call(_raise_value_error())

        # Nächster Call sollte auch durchkommen (inflight wurde decremented)
        result = await cb.call(_success_coro())
        assert result == "ok"
