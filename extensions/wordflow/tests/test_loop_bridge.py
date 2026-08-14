# -*- coding: utf-8 -*-
"""Tests G2/G3 loop_bridge."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.loop_bridge import (
    bridge_full,
    bridge_to_lock,
    bridge_with_answers,
)


class TestLoopBridge(unittest.TestCase):
    def test_bridge_to_lock_ok(self):
        raw = (
            "objective: bridge g2 lock\n"
            "success: lock ok\n"
            "constraint: 0% LLM\n"
        )
        r = bridge_to_lock(raw)
        self.assertTrue(r["ok"])
        self.assertIn("lock_id", r["lock"])

    def test_with_answers(self):
        raw = "objective: explicit answers\nsuccess: done\n"
        r = bridge_with_answers(raw, {"Q12_approver": "director"})
        self.assertTrue(r["ok"])

    def test_bridge_full(self):
        raw = (
            "objective: bridge g3 full path\n"
            "success: classify ok\n"
            "constraint: deterministic\n"
        )
        r = bridge_full(raw, task_hint="validate schema")
        self.assertIn("lock", r)
        self.assertIn("echo", r)
        self.assertIn("registers", r)
        self.assertIn("classification", r)
        self.assertEqual(r["stage"], "full")


if __name__ == "__main__":
    unittest.main()
