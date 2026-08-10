# -*- coding: utf-8 -*-
"""A-WF-04 tests — Sentinel gate."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wordflow.engine.goals_extractor import extract_goals_in  # noqa: E402
from wordflow.engine.input_normalizer import normalize_input_block  # noqa: E402
from wordflow.engine.sentinel import run_sentinel  # noqa: E402


def _raw(**kw):
    b = {
        "schema_version": "1.0",
        "block_id": "IB-S1",
        "source_type": "chat",
        "raw_text": "Implementar fingerprint control-layer ≤120 LOC",
        "quality_bar": "never_MVP",
        "goals_hint": ["fingerprint"],
        "priority": "P0",
        "constraints": {"loc_limit": 120, "success_criteria": "tests green"},
    }
    b.update(kw)
    return b


class TestSentinel(unittest.TestCase):
    def test_pass(self):
        raw = _raw()
        block = normalize_input_block(raw)
        goals = extract_goals_in(block)
        s = run_sentinel(raw, goals_in=goals)
        self.assertEqual(s["verdict"], "PASS")
        self.assertEqual(s["reason_codes"], [])

    def test_fail_schema(self):
        s = run_sentinel(None)
        self.assertEqual(s["verdict"], "FAIL")
        self.assertIn("MISSING_BLOCK", s["reason_codes"])

    def test_fail_never_mvp_no_criteria(self):
        s = run_sentinel(_raw(constraints={"loc_limit": 100}))
        self.assertEqual(s["verdict"], "FAIL")
        self.assertIn("L2_NO_SUCCESS_CRITERIA", s["reason_codes"])

    def test_fail_budget(self):
        s = run_sentinel(
            _raw(constraints={"loc_limit": 500, "success_criteria": "ok"})
        )
        self.assertEqual(s["verdict"], "FAIL")
        self.assertIn("L3_BUDGET_EXCEEDED", s["reason_codes"])

    def test_standard_soft_l2(self):
        s = run_sentinel(
            _raw(quality_bar="standard", constraints={"loc_limit": 100})
        )
        self.assertIn(s["verdict"], ("PASS", "FAIL"))
        self.assertIsNotNone(s["block"])

    def test_checks_populated(self):
        s = run_sentinel(_raw())
        names = [c["name"] for c in s["checks"]]
        self.assertIn("schema", names)
        self.assertIn("quality_bar", names)
        self.assertIn("refute", names)


if __name__ == "__main__":
    unittest.main()
