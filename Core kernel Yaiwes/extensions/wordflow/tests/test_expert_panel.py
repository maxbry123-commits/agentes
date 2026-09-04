# -*- coding: utf-8 -*-
"""Tests T29 ExpertPanel."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.expert_panel import ExpertPanel, RuleExpert, StaticExpert


class TestExpertPanel(unittest.TestCase):
    def test_collect_tally(self):
        panel = ExpertPanel(
            [
                StaticExpert("a", "arch", vote="APPROVE"),
                StaticExpert("b", "sec", vote="APPROVE"),
                RuleExpert(),
            ]
        )
        r = panel.collect("ship?", {"risk_score": 1})
        self.assertEqual(r["n"], 3)
        self.assertEqual(r["tally"].get("APPROVE"), 3)

    def test_rule_reject(self):
        panel = ExpertPanel([RuleExpert()])
        r = panel.collect("x", {"risk_high": True})
        self.assertEqual(r["opinions"][0]["vote"], "REJECT")


if __name__ == "__main__":
    unittest.main()
