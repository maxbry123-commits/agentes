# -*- coding: utf-8 -*-
"""Tests T30 Expert DecisionGate."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.expert_decision import decide_from_panel, panel_decide
from extensions.wordflow.engine.expert_panel import ExpertPanel, RuleExpert, StaticExpert


class TestExpertDecision(unittest.TestCase):
    def test_majority_allow(self):
        panel = ExpertPanel(
            [
                StaticExpert("1", "a", vote="APPROVE"),
                StaticExpert("2", "b", vote="APPROVE"),
                StaticExpert("3", "c", vote="ABSTAIN"),
            ]
        )
        d = panel_decide(panel, "ship")
        self.assertTrue(d["ok"])
        self.assertEqual(d["decision"], "ALLOW")
        self.assertEqual(d["decider"], "YAIWES")

    def test_reject_wins(self):
        panel = ExpertPanel(
            [
                StaticExpert("1", "a", vote="APPROVE"),
                RuleExpert(),
            ]
        )
        d = panel_decide(panel, "x", {"risk_high": True})
        self.assertFalse(d["ok"])
        self.assertEqual(d["decision"], "DENY")

    def test_empty_fail_closed(self):
        d = decide_from_panel({"opinions": [], "tally": {}, "n": 0})
        self.assertEqual(d["decision"], "DENY")


if __name__ == "__main__":
    unittest.main()
