# -*- coding: utf-8 -*-
"""Tests T27 EvidenceGraph."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.evidence_graph import EvidenceGraph


class TestEvidenceGraph(unittest.TestCase):
    def test_chain(self):
        g = EvidenceGraph(mission_id="m1")
        ids = g.add_chain(
            [
                ("mission", {"id": "m1"}),
                ("lock", {"lock_id": "L"}),
                ("sheriff", {"action": "ALLOW"}),
            ]
        )
        self.assertEqual(len(ids), 3)
        self.assertEqual(len(g.edges), 2)
        snap = g.snapshot()
        self.assertEqual(snap["node_count"], 3)

    def test_verify(self):
        g = EvidenceGraph()
        n = g.add_node("note", {"x": 1})
        self.assertTrue(g.verify_node(n["node_id"], {"x": 1}))
        self.assertFalse(g.verify_node(n["node_id"], {"x": 2}))

    def test_link_requires_nodes(self):
        g = EvidenceGraph()
        a = g.add_node("note", "a")
        with self.assertRaises(KeyError):
            g.link(a["node_id"], "missing")


if __name__ == "__main__":
    unittest.main()
