# -*- coding: utf-8 -*-
"""Tests C-21 Mission Planner — offline, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.planner.mission_planner import TaskGraphError, plan_from_council


class TestMissionPlanner(unittest.TestCase):
    def test_plan_from_strings(self):
        council = {
            "mission_id": "m1",
            "plan": ["normalize", "analyze", "compile"],
            "roles": ["architect"],
            "risks": ["license"],
        }
        g = plan_from_council(council)
        self.assertTrue(g["ok"])
        self.assertEqual(g["node_count"], 3)
        self.assertEqual(g["nodes"][0]["id"], "T_00")
        self.assertEqual(g["nodes"][1]["depends_on"], ["T_00"])
        self.assertEqual(len(g["edges"]), 2)
        self.assertEqual(g["llm_control"], "DENY")

    def test_plan_from_dicts(self):
        council = {
            "plan": [
                {"title": "acquire", "priority": 1},
                {"title": "promote", "priority": 2},
            ]
        }
        g = plan_from_council(council)
        self.assertEqual(g["nodes"][0]["title"], "acquire")
        self.assertEqual(g["nodes"][0]["meta"].get("priority"), 1)

    def test_empty_plan_raises(self):
        with self.assertRaises(TaskGraphError) as ctx:
            plan_from_council({"plan": []})
        self.assertEqual(ctx.exception.reason_code, "COUNCIL_PLAN_EMPTY")

    def test_not_object_raises(self):
        with self.assertRaises(TaskGraphError) as ctx:
            plan_from_council(None)  # type: ignore
        self.assertEqual(ctx.exception.reason_code, "COUNCIL_NOT_OBJECT")

    def test_graph_hash_stable(self):
        c = {"plan": ["a", "b"]}
        g1 = plan_from_council(c)
        g2 = plan_from_council(c)
        self.assertEqual(g1["graph_hash"], g2["graph_hash"])


if __name__ == "__main__":
    unittest.main()
