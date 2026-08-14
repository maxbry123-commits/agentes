# -*- coding: utf-8 -*-
"""Tests V1-03 bitacora on V1 turns."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.bitacora import BitacoraStore
from extensions.wordflow.engine.orchestrator_v1 import OrchestratorV1


class TestOrchestratorV1Bitacora(unittest.TestCase):
    def test_happy_appends(self):
        b = BitacoraStore()
        orch = OrchestratorV1(bitacora=b)
        r = orch.run_turn(
            "crear validacion",
            "validacion",
            operation="READ_LOCAL",
            risk_score=1,
            band="low",
        )
        self.assertGreaterEqual(b.length, 1)
        chain = b.verify_chain()
        self.assertTrue(chain.get("ok"), msg=str(chain))
        if r.get("ok"):
            self.assertTrue(r["bitacora_chain"]["ok"])

    def test_fail_also_logs(self):
        b = BitacoraStore()
        orch = OrchestratorV1(bitacora=b)
        orch.run_turn("x", "x", operation="NO_EXISTE")
        self.assertGreaterEqual(b.length, 1)


if __name__ == "__main__":
    unittest.main()
