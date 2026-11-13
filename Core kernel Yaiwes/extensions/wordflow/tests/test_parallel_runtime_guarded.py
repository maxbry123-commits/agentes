# -*- coding: utf-8 -*-
"""Tests T23 GuardedParallelRuntime."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.circuit_breaker import CircuitBreaker
from extensions.wordflow.engine.parallel_runtime_guarded import GuardedParallelRuntime
from extensions.wordflow.engine.retry_policy import RetryPolicy


class TestGuardedParallelRuntime(unittest.TestCase):
    def test_retry_recovers(self):
        state = {"n": 0}
        rt = GuardedParallelRuntime(
            n_workers=1,
            retry=RetryPolicy(max_attempts=3, strategy="fixed", base_delay_s=0),
        )
        rt.submit(task_id="t")

        def handler(ctx):
            state["n"] += 1
            return state["n"] >= 2

        result = rt.run(handler)
        self.assertTrue(result["executions"][0]["ok"])
        self.assertEqual(state["n"], 2)

    def test_circuit_opens(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout_s=100)
        rt = GuardedParallelRuntime(
            n_workers=1,
            retry=RetryPolicy(max_attempts=1),
            circuit=cb,
        )
        rt.submit(task_id="a")
        rt.submit(task_id="b")
        rt.submit(task_id="c")
        result = rt.run(lambda ctx: False)
        self.assertEqual(cb.state, "OPEN")
        failed = sum(1 for e in result["executions"] if not e["ok"])
        self.assertGreaterEqual(failed, 2)


if __name__ == "__main__":
    unittest.main()
