# -*- coding: utf-8 -*-
"""Tests T21 RetryPolicy."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.retry_policy import RetryExhaustedError, RetryPolicy


class TestRetryPolicy(unittest.TestCase):
    def test_succeeds_first_try(self):
        p = RetryPolicy(max_attempts=3)
        self.assertEqual(p.run(lambda: 42), 42)

    def test_retry_then_ok(self):
        state = {"n": 0}

        def flaky():
            state["n"] += 1
            if state["n"] < 3:
                raise ValueError("fail")
            return "ok"

        delays: list[float] = []
        p = RetryPolicy(max_attempts=5, strategy="fixed", base_delay_s=0.5)
        result = p.run(flaky, sleeper=delays.append)
        self.assertEqual(result, "ok")
        self.assertEqual(delays, [0.5, 0.5])

    def test_exhausted(self):
        p = RetryPolicy(max_attempts=2, strategy="linear", base_delay_s=1.0)
        with self.assertRaises(RetryExhaustedError):
            p.run(lambda: (_ for _ in ()).throw(RuntimeError("x")), sleeper=lambda d: None)

    def test_exponential_plan(self):
        p = RetryPolicy(max_attempts=4, strategy="exponential", base_delay_s=1.0, max_delay_s=10)
        plan = p.plan()
        self.assertEqual([x["delay_s"] for x in plan], [1.0, 2.0, 4.0])

    def test_max_delay_cap(self):
        p = RetryPolicy(max_attempts=10, strategy="exponential", base_delay_s=2.0, max_delay_s=5.0)
        self.assertEqual(p.delay_for_attempt(5), 5.0)


if __name__ == "__main__":
    unittest.main()
