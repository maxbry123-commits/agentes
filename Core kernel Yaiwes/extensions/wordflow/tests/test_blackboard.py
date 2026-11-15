# -*- coding: utf-8 -*-
"""Tests C-23 Blackboard — offline, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.state.blackboard import Blackboard, BlackboardError


class TestBlackboard(unittest.TestCase):
    def test_goals_and_tasks(self):
        bb = Blackboard(mission_id="m1")
        bb.set_goal("g1", {"text": "ship C-23"})
        bb.upsert_task("T_00", "PENDING", title="init")
        bb.upsert_task("T_00", "RUNNING")
        self.assertEqual(bb.tasks["T_00"]["status"], "RUNNING")
        self.assertEqual(bb.goals["g1"]["text"], "ship C-23")

    def test_evidence_resources_blockers(self):
        bb = Blackboard()
        bb.add_evidence({"ref": "e1"})
        bb.set_resource("r1", "AVAILABLE", kind="repo")
        bb.add_blocker("b1", "license")
        self.assertTrue(bb.has_blockers())
        bb.clear_blocker("b1")
        self.assertFalse(bb.has_blockers())
        snap = bb.snapshot()
        self.assertEqual(snap["llm_control"], "DENY")
        self.assertEqual(len(snap["evidence"]), 1)

    def test_pending_tasks(self):
        bb = Blackboard()
        bb.upsert_task("a", "PENDING")
        bb.upsert_task("b", "DONE")
        self.assertEqual(bb.pending_tasks(), ["a"])

    def test_empty_ids_raise(self):
        bb = Blackboard()
        with self.assertRaises(BlackboardError):
            bb.set_goal("", {})
        with self.assertRaises(BlackboardError):
            bb.upsert_task("", "PENDING")


if __name__ == "__main__":
    unittest.main()
