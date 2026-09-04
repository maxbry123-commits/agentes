# -*- coding: utf-8 -*-
"""Tests C-17 repair_gate — offline, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.repair_gate import RepairGate, RepairGateError


class TestRepairGate(unittest.TestCase):
    def test_allows_under_max(self):
        g = RepairGate(policy={"limits": {"max_repair": 2}})
        self.assertTrue(g.can_repair("t1")["ok"])
        g.record_attempt("t1")
        g.record_attempt("t1")
        self.assertFalse(g.can_repair("t1")["ok"])

    def test_raises_over_max(self):
        g = RepairGate(policy={"limits": {"max_repair": 1}})
        g.record_attempt("t")
        with self.assertRaises(RepairGateError):
            g.record_attempt("t")

    def test_reset(self):
        g = RepairGate(policy={"limits": {"max_repair": 1}})
        g.record_attempt("t")
        g.reset("t")
        self.assertTrue(g.can_repair("t")["ok"])


if __name__ == "__main__":
    unittest.main()
