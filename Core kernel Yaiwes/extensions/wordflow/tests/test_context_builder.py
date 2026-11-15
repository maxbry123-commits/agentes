# -*- coding: utf-8 -*-
"""Tests C-25 Context Builder — offline, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.context.builder import ContextError, build_context
from extensions.wordflow.state.blackboard import Blackboard


class TestContextBuilder(unittest.TestCase):
    def test_build_with_lock(self):
        r = build_context(goal_lock={"lock_id": "L1", "goals_in": ["g"]})
        self.assertTrue(r["ok"])
        self.assertEqual(r["context"]["mission_id"], "L1")
        self.assertEqual(r["context"]["llm_control"], "DENY")
        self.assertIn("context_hash", r["context"])

    def test_build_with_mission_and_blackboard(self):
        bb = Blackboard(mission_id="m9")
        bb.upsert_task("T_00", "PENDING")
        r = build_context(
            mission={"mission_id": "m9", "lock": {"lock_id": "m9"}},
            blackboard=bb,
            evidence=[{"ref": "e1"}],
            policies={"deploy": "deny_force"},
            resources={"repo": {"state": "AVAILABLE"}},
        )
        ctx = r["context"]
        self.assertEqual(ctx["blackboard_slice"]["tasks"]["T_00"]["status"], "PENDING")
        self.assertEqual(ctx["policies"]["deploy"], "deny_force")

    def test_missing_mission_and_lock(self):
        with self.assertRaises(ContextError) as ctx:
            build_context()
        self.assertEqual(ctx.exception.reason_code, "NO_MISSION_OR_LOCK")

    def test_hash_stable(self):
        lock = {"lock_id": "X"}
        a = build_context(goal_lock=lock)
        b = build_context(goal_lock=lock)
        self.assertEqual(a["context"]["context_hash"], b["context"]["context_hash"])


if __name__ == "__main__":
    unittest.main()
