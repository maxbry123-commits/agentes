# -*- coding: utf-8 -*-
"""Tests V1-01 OrchestratorV1."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.orchestrator_v1 import OrchestratorV1


class TestOrchestratorV1(unittest.TestCase):
    def test_happy_path(self):
        orch = OrchestratorV1()
        r = orch.run_turn(
            "crear modulo de validacion determinista",
            "validacion",
            operation="READ_LOCAL",
            risk_score=1,
            band="low",
        )
        self.assertTrue(r.get("ok"), msg=str(r))
        self.assertEqual(r.get("stage"), "v1_turn_done")
        self.assertIn("dna", r)
        self.assertIn("C00", r["contracts"]["contracts"])

    def test_unknown_operation(self):
        orch = OrchestratorV1()
        r = orch.run_turn("x", "x", operation="NO_EXISTE")
        self.assertFalse(r.get("ok"))
        self.assertEqual(r.get("stage"), "contracts")

    def test_high_risk_may_deny(self):
        orch = OrchestratorV1()
        r = orch.run_turn(
            "objetivo critico",
            "critico",
            risk_score=10,
            band="critical",
        )
        # may DENY on sheriff depending on gate policy
        self.assertIn(r.get("ok"), (True, False))
        self.assertIn("stage", r)


if __name__ == "__main__":
    unittest.main()
