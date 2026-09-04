# -*- coding: utf-8 -*-
"""Tests T47 Orchestrator."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.orchestrator import Orchestrator


class TestOrchestrator(unittest.TestCase):
    def test_turn_allow(self):
        orch = Orchestrator()
        r = orch.run_turn(
            "objective: orch t47\nsuccess: panel\nconstraint: 0% LLM\n",
            "approve deterministic plan",
            risk_score=1,
            task_class="DETERMINISTIC",
        )
        self.assertIn("state", r)
        self.assertIn("panel", r)

    def test_sheriff_stop(self):
        orch = Orchestrator()
        r = orch.run_turn(
            "objective: stop\nsuccess: no\n",
            "ship",
            risk_score=9,
            band="quarantine",
        )
        self.assertFalse(r["ok"])
        self.assertEqual(r["stage"], "sheriff")


if __name__ == "__main__":
    unittest.main()
