# -*- coding: utf-8 -*-
"""Tests T19 CircuitBreaker."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.circuit_breaker import CircuitBreaker, CircuitOpenError


class FakeClock:
    def __init__(self, t: float = 0.0):
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


class TestCircuitBreaker(unittest.TestCase):
    def test_opens_after_threshold(self):
        clk = FakeClock()
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout_s=10, clock=clk)

        def fail():
            raise RuntimeError("x")

        for _ in range(3):
            with self.assertRaises(RuntimeError):
                cb.call(fail)
        self.assertEqual(cb.state, "OPEN")
        with self.assertRaises(CircuitOpenError):
            cb.call(lambda: 1)

    def test_half_open_to_closed(self):
        clk = FakeClock()
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout_s=5, clock=clk)
        for _ in range(2):
            with self.assertRaises(RuntimeError):
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError()))
        clk.advance(5.0)
        self.assertTrue(cb.allow())
        self.assertEqual(cb.state, "HALF_OPEN")
        self.assertEqual(cb.call(lambda: "ok"), "ok")
        self.assertEqual(cb.state, "CLOSED")

    def test_half_open_fail_reopens(self):
        clk = FakeClock()
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout_s=3, clock=clk)
        with self.assertRaises(RuntimeError):
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError()))
        clk.advance(3.0)
        with self.assertRaises(RuntimeError):
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError()))
        self.assertEqual(cb.state, "OPEN")


if __name__ == "__main__":
    unittest.main()
