# -*- coding: utf-8 -*-
"""Tests T33 RecoveryEngine."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.recovery import RecoveryAction, RecoveryEngine, choose_action
from extensions.wordflow.engine.retry_policy import RetryPolicy


class TestRecovery(unittest.TestCase):
    def test_choose_retry(self):
        a = choose_action(
            attempts=0, max_attempts=3, has_checkpoint=False, sandbox_dead=False, circuit_open=False
        )
        self.assertEqual(a, RecoveryAction.RETRY)

    def test_choose_escalate_circuit(self):
        a = choose_action(
            attempts=0, max_attempts=3, has_checkpoint=False, sandbox_dead=False, circuit_open=True
        )
        self.assertEqual(a, RecoveryAction.ESCALATE)

    def test_run_retry_ok(self):
        eng = RecoveryEngine(retry=RetryPolicy(max_attempts=2))
        box = {"n": 0}

        def fn():
            box["n"] += 1
            if box["n"] < 2:
                raise RuntimeError("once")
            return "ok"

        r = eng.run_with_retry(fn)
        self.assertTrue(r["ok"])


if __name__ == "__main__":
    unittest.main()
