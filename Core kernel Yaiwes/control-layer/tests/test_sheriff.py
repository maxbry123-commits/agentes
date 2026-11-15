# -*- coding: utf-8 -*-
"""tests/test_sheriff.py — A7"""
from __future__ import annotations
import sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from control.compiler import compile_plan
from sheriff.states import SheriffState, can_transition, state_from_band
from sheriff.decision import decide

class TestSheriff(unittest.TestCase):
    def test_green_allow(self):
        plan = compile_plan("read local config list show")
        d = decide(plan)
        self.assertEqual(d.state, SheriffState.GREEN)
        self.assertEqual(d.action, "ALLOW")

    def test_high_risk_deny(self):
        plan = compile_plan("delete force token secret https://api.example.com")
        d = decide(plan)
        self.assertIn(d.state, (SheriffState.RED, SheriffState.ORANGE))
        self.assertIn(d.action, ("DENY", "ESCALATE"))

    def test_transition_rules(self):
        self.assertTrue(can_transition(SheriffState.GREEN, SheriffState.YELLOW))
        self.assertFalse(can_transition(SheriffState.GREEN, SheriffState.BLACK))
        self.assertTrue(can_transition(SheriffState.BLACK, SheriffState.BLACK))

    def test_band_map(self):
        self.assertEqual(state_from_band("normal", 1), SheriffState.GREEN)
        self.assertEqual(state_from_band("sheriff_check", 5), SheriffState.YELLOW)
        self.assertEqual(state_from_band("quarantine", 9), SheriffState.RED)

    def test_conflict_deny(self):
        plan = compile_plan("read")
        plan.ok = False
        plan.conflicts = ["C47 forbids C99_UNSAFE"]
        d = decide(plan)
        self.assertEqual(d.action, "DENY")

if __name__ == "__main__":
    unittest.main(verbosity=2)
