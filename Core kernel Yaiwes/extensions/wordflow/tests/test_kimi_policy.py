# -*- coding: utf-8 -*-
"""Tests D8 kimi_policy."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.kimi_policy import (
    confidence_gate,
    deliberation_budget,
    may_invoke_llm,
)


class TestKimiPolicy(unittest.TestCase):
    def test_budget_low_no_llm(self):
        b = deliberation_budget("low")
        self.assertTrue(b["ok"])
        self.assertFalse(b["allow_llm"])

    def test_llm_denied_by_control(self):
        r = may_invoke_llm(task_class="REASONING", budget_level="high", llm_control="DENY")
        self.assertFalse(r["invoke"])

    def test_confidence(self):
        self.assertTrue(confidence_gate(0.8, evidence_count=1)["ok"])
        self.assertFalse(confidence_gate(0.2, evidence_count=1)["ok"])


if __name__ == "__main__":
    unittest.main()
