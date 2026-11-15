# -*- coding: utf-8 -*-
"""tests/test_graph.py — A4"""
from __future__ import annotations
import sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from control.graph import build_graph, expand_deps, topo_sort
from control.reverse import reverse_check

class TestGraph(unittest.TestCase):
    def test_expand(self):
        s = expand_deps(["C04"])
        self.assertIn("C03", s)
        self.assertIn("C00", s)

    def test_topo_order(self):
        order = build_graph(["C04", "C28"])
        self.assertLess(order.index("C00"), order.index("C03"))
        self.assertLess(order.index("C03"), order.index("C04"))

    def test_determinism(self):
        a = build_graph(["C45", "C33"])
        b = build_graph(["C45", "C33"])
        self.assertEqual(a, b)

    def test_reverse_ok(self):
        ok, msgs = reverse_check(["C03", "C28"])
        self.assertTrue(ok)
        self.assertEqual(msgs, [])

    def test_reverse_conflict(self):
        ok, msgs = reverse_check(["C47", "C99_UNSAFE"])
        self.assertFalse(ok)
        self.assertTrue(any("forbids" in m for m in msgs))

if __name__ == "__main__":
    unittest.main(verbosity=2)
