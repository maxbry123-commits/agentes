# -*- coding: utf-8 -*-
"""V1-07 e2e — Sim A happy · Sim B sheriff DENY · Sim C contracts fail."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from extensions.wordflow.engine.bitacora import BitacoraStore
from extensions.wordflow.engine.entrypoint_v1 import run_v1
from extensions.wordflow.engine.orchestrator_v1 import OrchestratorV1


class TestV1E2E(unittest.TestCase):
    def test_sim_a_happy(self):
        """Sim A: mission→C00→panel→DNA→ok"""
        b = BitacoraStore()
        orch = OrchestratorV1(bitacora=b)
        r = run_v1(
            "crear modulo de validacion determinista sin llm",
            topic="validacion",
            operation="READ_LOCAL",
            risk_score=1,
            band="low",
            orchestrator=orch,
        )
        self.assertTrue(r.get("ok"), msg=str(r))
        self.assertEqual(r.get("stage"), "v1_turn_done")
        self.assertIn("dna", r)
        self.assertTrue(r["dna"].get("dna_hash"))
        self.assertIn("C00", r["contracts"]["contracts"])
        self.assertIsNone(r.get("recovery"))
        self.assertGreaterEqual(r.get("bitacora_len", 0), 1)
        self.assertTrue(r["bitacora_chain"]["ok"])
        self.assertGreaterEqual(r["evidence"]["node_count"], 2)

    def test_sim_b_sheriff_deny(self):
        """Sim B: risk high → DETENIDO + recovery"""
        orch = OrchestratorV1()
        r = run_v1(
            "operacion de alto riesgo",
            topic="critico",
            operation="READ_LOCAL",
            risk_score=10,
            band="quarantine",
            attempts=0,
            orchestrator=orch,
        )
        self.assertFalse(r.get("ok"))
        self.assertEqual(r.get("stage"), "sheriff")
        self.assertIn("recovery", r)
        self.assertIn(r["recovery"]["action"], ("RETRY", "ESCALATE", "CHECKPOINT_RESTORE"))

    def test_sim_c_bad_operation(self):
        """Sim C proxy: bad contracts path → REPAIR + recovery (panel deny hard to force)"""
        orch = OrchestratorV1()
        r = run_v1(
            "tarea generica",
            topic="x",
            operation="NO_EXISTE_OP",
            risk_score=1,
            band="low",
            attempts=2,
            orchestrator=orch,
        )
        self.assertFalse(r.get("ok"))
        self.assertEqual(r.get("stage"), "contracts")
        self.assertIn("recovery", r)

    def test_sim_c_panel_deny_mocked(self):
        """Sim C: panel DENY → recovery + REPAIR state"""
        orch = OrchestratorV1()

        def _deny(*_a, **_k):
            return {"ok": False, "decision": "DENY", "reason": "MOCK"}

        with patch(
            "extensions.wordflow.engine.orchestrator_v1.route_and_decide",
            side_effect=_deny,
        ):
            r = orch.run_turn(
                "crear algo",
                "tema",
                operation="READ_LOCAL",
                risk_score=1,
                band="low",
                attempts=1,
            )
        self.assertFalse(r.get("ok"))
        self.assertEqual(r.get("stage"), "panel")
        self.assertIn("recovery", r)


if __name__ == "__main__":
    unittest.main()
