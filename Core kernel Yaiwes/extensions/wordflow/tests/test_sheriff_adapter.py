# -*- coding: utf-8 -*-
"""Tests T25 sheriff_adapter."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.loop_bridge import bridge_to_lock
from extensions.wordflow.engine.sheriff_adapter import (
    SheriffState,
    can_transition,
    gate_lock,
    state_from_band,
)


class TestSheriffAdapter(unittest.TestCase):
    def test_five_states(self):
        names = {s.value for s in SheriffState}
        self.assertEqual(names, {"GREEN", "YELLOW", "ORANGE", "RED", "BLACK"})

    def test_band_mapping(self):
        self.assertEqual(state_from_band("", 0), SheriffState.GREEN)
        self.assertEqual(state_from_band("sheriff_check", 5), SheriffState.YELLOW)
        self.assertEqual(state_from_band("quarantine", 9), SheriffState.RED)

    def test_gate_lock_allow(self):
        lock = bridge_to_lock(
            "objective: sheriff t25\nsuccess: green\nconstraint: 0% LLM\n"
        )["lock"]
        g = gate_lock(lock, risk_score=1)
        self.assertTrue(g["passed"])
        self.assertEqual(g["state"], "GREEN")

    def test_gate_lock_deny_red(self):
        lock = bridge_to_lock(
            "objective: high risk\nsuccess: deny\nconstraint: none\n"
        )["lock"]
        g = gate_lock(lock, risk_score=9, band="quarantine")
        self.assertFalse(g["passed"])
        self.assertEqual(g["action"], "DENY")

    def test_black_no_exit(self):
        self.assertFalse(can_transition(SheriffState.BLACK, SheriffState.GREEN))


if __name__ == "__main__":
    unittest.main()
