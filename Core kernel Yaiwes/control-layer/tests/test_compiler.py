# -*- coding: utf-8 -*-
"""tests/test_compiler.py — A5"""
from __future__ import annotations
import sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from control.compiler import compile_plan
from control.normalizer import normalize

class TestCompiler(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalize("  Hello   WORLD  "), "hello world")
        self.assertEqual(normalize({"b": 1, "a": 2}), '{"a": 2, "b": 1}')

    def test_compile_read(self):
        plan = compile_plan("read local config list show")
        self.assertTrue(plan.ok)
        self.assertIn("C00", plan.contracts)
        self.assertLessEqual(plan.threat.risk_score, 3)

    def test_compile_install(self):
        plan = compile_plan("install package from https://pypi.org with token")
        self.assertTrue(plan.ok)
        self.assertTrue(plan.fingerprint.writes)
        self.assertGreaterEqual(plan.threat.risk_score, 4)
        self.assertIn("C45", plan.contracts)

    def test_determinism(self):
        a = compile_plan("mount load_extension")
        b = compile_plan("mount load_extension")
        self.assertEqual(a.to_dict(), b.to_dict())

    def test_contracts_ordered(self):
        plan = compile_plan("write save file")
        self.assertLess(plan.contracts.index("C00"), plan.contracts.index("C03"))

if __name__ == "__main__":
    unittest.main(verbosity=2)
