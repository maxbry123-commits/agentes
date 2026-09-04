# -*- coding: utf-8 -*-
"""tests/test_integration.py — A10 pipeline fingerprint→sheriff"""
from __future__ import annotations
import sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from control.compiler import compile_plan
from sheriff.gate import gate
from sheriff.states import SheriffState

class TestIntegration(unittest.TestCase):
    def test_end_to_end_read_allow(self):
        plan = compile_plan("read local config list show")
        g = gate(plan)
        self.assertTrue(plan.ok)
        self.assertTrue(g.passed)
        self.assertEqual(g.decision.action, "ALLOW")
        self.assertEqual(g.decision.state, SheriffState.GREEN)
        self.assertIn("C00", plan.contracts)
        self.assertLessEqual(plan.threat.risk_score, 3)

    def test_end_to_end_install_checked(self):
        plan = compile_plan("install package from https://pypi.org with token")
        g = gate(plan)
        self.assertTrue(plan.ok)
        self.assertTrue(plan.fingerprint.writes)
        self.assertTrue(plan.fingerprint.network)
        self.assertTrue(plan.fingerprint.credentials)
        self.assertIn("C45", plan.contracts)
        self.assertGreaterEqual(plan.threat.risk_score, 4)
        self.assertIn(g.decision.action, ("ALLOW", "DENY", "ESCALATE"))

    def test_end_to_end_delete_deny(self):
        plan = compile_plan("delete force token secret https://api.example.com")
        g = gate(plan)
        self.assertFalse(g.passed)
        self.assertEqual(g.decision.action, "DENY")
        self.assertGreaterEqual(plan.threat.risk_score, 8)

    def test_mount_extension_path(self):
        plan = compile_plan("mount load_extension register_extension")
        g = gate(plan)
        self.assertTrue(plan.ok)
        self.assertIn("C82", plan.contracts)
        self.assertIn("C00", plan.contracts)

    def test_determinism_full(self):
        a = gate(compile_plan("write save file")).to_dict()
        b = gate(compile_plan("write save file")).to_dict()
        self.assertEqual(a, b)

    def test_ficha_exists(self):
        ficha = ROOT / "ficha.v2.json"
        manifest = ROOT / "manifest.yaml"
        self.assertTrue(ficha.is_file())
        self.assertTrue(manifest.is_file())

if __name__ == "__main__":
    unittest.main(verbosity=2)
