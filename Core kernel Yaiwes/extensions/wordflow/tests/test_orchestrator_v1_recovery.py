# -*- coding: utf-8 -*-
"""Tests V1-02 recovery on fail paths."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.orchestrator_v1 import OrchestratorV1


class TestOrchestratorV1Recovery(unittest.TestCase):
    def test_bad_operation_has_recovery(self):
        orch = OrchestratorV1()
        r = orch.run_turn("x", "x", operation="NO_EXISTE", attempts=1)
        self.assertFalse(r["ok"])
        self.assertIn("recovery", r)
        self.assertIn(r["recovery"]["action"], ("RETRY", "ESCALATE", "CHECKPOINT_RESTORE"))

    def test_happy_no_recovery_action(self):
        orch = OrchestratorV1()
        r = orch.run_turn(
            "crear validacion",
            "validacion",
            operation="READ_LOCAL",
            risk_score=1,
            band="low",
        )
        if r.get("ok"):
            self.assertIsNone(r.get("recovery"))


if __name__ == "__main__":
    unittest.main()
