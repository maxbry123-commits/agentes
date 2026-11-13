# -*- coding: utf-8 -*-
"""Tests T31 ExpertRouter."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.expert_router import build_panel_for_class, route_and_decide


class TestExpertRouter(unittest.TestCase):
    def test_code_roster(self):
        p = build_panel_for_class("CODE")
        # 3 static + rule
        self.assertEqual(len(p.experts), 4)

    def test_route_allow(self):
        r = route_and_decide("merge?", task_class="DETERMINISTIC", context={"risk_score": 1})
        self.assertEqual(r["task_class"], "DETERMINISTIC")
        self.assertTrue(r["ok"])

    def test_route_reject_risk(self):
        r = route_and_decide("ship?", task_class="CODE", context={"risk_high": True})
        self.assertFalse(r["ok"])
        self.assertEqual(r["decision"], "DENY")


if __name__ == "__main__":
    unittest.main()
