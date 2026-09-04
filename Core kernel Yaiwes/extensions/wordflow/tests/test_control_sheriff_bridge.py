# -*- coding: utf-8 -*-
"""Tests D6 control_sheriff_bridge."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.control_sheriff_bridge import gate_c00
from extensions.wordflow.engine.loop_bridge import bridge_to_lock


class TestControlSheriffBridge(unittest.TestCase):
    def test_c00_required(self):
        lock = bridge_to_lock(
            "objective: d6 c00\nsuccess: pass\nconstraint: 0% LLM\n"
        )["lock"]
        g = gate_c00(lock, contracts=["C01"], require_c00=True)
        self.assertFalse(g["passed"])
        self.assertEqual(g["reason"], "MISSING_C00")

    def test_c00_ok_fallback(self):
        lock = bridge_to_lock(
            "objective: d6 ok\nsuccess: allow\nconstraint: green\n"
        )["lock"]
        g = gate_c00(lock, contracts=["C00", "C01"], risk_score=0)
        self.assertTrue(g["passed"])

    def test_lock_fail(self):
        g = gate_c00({"lock_id": "x"}, contracts=["C00"])
        self.assertFalse(g["passed"])


if __name__ == "__main__":
    unittest.main()
