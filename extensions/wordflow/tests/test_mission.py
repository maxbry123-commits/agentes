# -*- coding: utf-8 -*-
"""Tests T26 Mission=GoalLock."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.mission import enforce_mission, mission_from_raw


class TestMission(unittest.TestCase):
    def test_mission_id_is_lock(self):
        m = mission_from_raw(
            "objective: mission t26\nsuccess: enforce\nconstraint: 0% LLM\n"
        )
        self.assertTrue(m["ok"])
        self.assertEqual(m["mission_id"], m["lock"]["lock_id"])

    def test_enforce_allow(self):
        m = mission_from_raw(
            "objective: allow path\nsuccess: ok\nconstraint: green\n"
        )
        e = enforce_mission(m, risk_score=0)
        self.assertTrue(e["ok"])

    def test_enforce_deny_risk(self):
        m = mission_from_raw(
            "objective: risky\nsuccess: deny\nconstraint: none\n"
        )
        e = enforce_mission(m, risk_score=9, band="quarantine")
        self.assertFalse(e["ok"])
        self.assertEqual(e["action"], "DENY")

    def test_mismatch_id(self):
        m = mission_from_raw("objective: x\nsuccess: y\n")
        m["mission_id"] = "other"
        e = enforce_mission(m)
        self.assertFalse(e["ok"])
        self.assertEqual(e["reason"], "MISSION_ID_MISMATCH")


if __name__ == "__main__":
    unittest.main()
