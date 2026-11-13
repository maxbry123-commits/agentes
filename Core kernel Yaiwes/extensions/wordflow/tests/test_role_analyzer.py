# -*- coding: utf-8 -*-
"""Tests C-12 role_analyzer — offline, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.role_analyzer import (
    analyze_available_motors,
    build_council_contract,
)
from extensions.wordflow.planner.mission_planner import plan_from_council


class TestRoleAnalyzer(unittest.TestCase):
    def test_analyze_code_class(self):
        r = analyze_available_motors(task_class="CODE")
        self.assertTrue(r["ok"])
        self.assertIn("architect", r["selected_roles"])
        self.assertEqual(r["llm_control"], "DENY")

    def test_registered_override(self):
        reg = {"architect": {"api": "internal", "cost": 0}}
        r = analyze_available_motors(reg, task_class="CODE")
        self.assertEqual(r["available_motors"]["architect"]["api"], "internal")

    def test_council_contract_to_planner(self):
        c = build_council_contract(
            topic="ship",
            plan=["acquire", "compile", "deploy"],
            task_class="CODE",
            mission_id="m1",
            risks=["license"],
        )
        self.assertTrue(c["ok"])
        g = plan_from_council(c)
        self.assertTrue(g["ok"])
        self.assertEqual(g["node_count"], 3)

    def test_empty_plan(self):
        c = build_council_contract(topic="x", plan=[])
        self.assertFalse(c["ok"])


if __name__ == "__main__":
    unittest.main()
