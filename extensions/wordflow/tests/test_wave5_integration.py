# -*- coding: utf-8 -*-
"""T32 WAVE-5 integration."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.wave5_runtime import run_with_panel


class TestWave5Integration(unittest.TestCase):
    def test_allow_path(self):
        r = run_with_panel(
            "objective: wave5 panel\nsuccess: decide\nconstraint: 0% LLM\n",
            "approve plan?",
            risk_score=1,
            task_class="DETERMINISTIC",
        )
        self.assertTrue(r["ok"])
        self.assertEqual(r["decision"]["decision"], "ALLOW")

    def test_sheriff_blocks(self):
        r = run_with_panel(
            "objective: blocked\nsuccess: no\nconstraint: none\n",
            "ship?",
            risk_score=9,
            band="quarantine",
        )
        self.assertFalse(r["ok"])
        self.assertEqual(r["stage"], "sheriff")

    def test_panel_reject(self):
        r = run_with_panel(
            "objective: high risk panel\nsuccess: deny\nconstraint: none\n",
            "deploy?",
            risk_score=0,
            task_class="CODE",
            context={"risk_high": True},
        )
        self.assertFalse(r["ok"])
        self.assertEqual(r["decision"]["decision"], "DENY")


if __name__ == "__main__":
    unittest.main()
