# -*- coding: utf-8 -*-
"""tests/test_gate.py — A8"""
from __future__ import annotations
import sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from control.compiler import compile_plan
from sheriff.gate import gate, load_policy

class TestGate(unittest.TestCase):
    def test_policy_loads(self):
        p = load_policy()
        self.assertTrue(p.get("fail_closed"))
        self.assertTrue(len(p.get("checks", [])) >= 4)

    def test_gate_allow_read(self):
        plan = compile_plan("read local config list show")
        g = gate(plan)
        self.assertTrue(g.passed)
        self.assertEqual(g.decision.action, "ALLOW")
        self.assertIn("C00", plan.contracts)

    def test_gate_deny_high(self):
        plan = compile_plan("delete force token secret https://api.example.com")
        g = gate(plan)
        self.assertFalse(g.passed)
        self.assertEqual(g.decision.action, "DENY")

    def test_gate_fail_closed_no_c00(self):
        plan = compile_plan("read")
        plan.contracts = [c for c in plan.contracts if c != "C00"]
        g = gate(plan)
        self.assertFalse(g.passed)
        self.assertIn("has_c00", g.failed_checks)

    def test_determinism(self):
        plan = compile_plan("write save file")
        a = gate(plan).to_dict()
        b = gate(plan).to_dict()
        self.assertEqual(a, b)

if __name__ == "__main__":
    unittest.main(verbosity=2)
