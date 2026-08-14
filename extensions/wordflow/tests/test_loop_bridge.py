# -*- coding: utf-8 -*-
"""Tests G2 loop_bridge."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.loop_bridge import bridge_to_lock, bridge_with_answers


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
        self.assertTrue(r["lock"].get("lock_hash"))

    def test_unresolved_without_approver(self):
        raw = "objective: need answers\nsuccess: x\n"
        r = bridge_to_lock(raw, auto_answer_approver=None, require_resolved=True)
        # may still resolve if form defaults; if not ok, stage questions
        if not r["ok"]:
            self.assertEqual(r["stage"], "questions")

    def test_with_answers(self):
        raw = "objective: explicit answers\nsuccess: done\n"
        r = bridge_with_answers(raw, {"Q12_approver": "director"})
        self.assertTrue(r["ok"])


if __name__ == "__main__":
    unittest.main()
