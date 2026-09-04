# -*- coding: utf-8 -*-
"""A-WF-08 tests — VersionSelector."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wordflow.engine.version_selector import score_candidate, select_best  # noqa: E402


class TestVersionSelector(unittest.TestCase):
    def test_score_high(self):
        c = {
            "has_tests": True,
            "has_ci": True,
            "has_schema": True,
            "has_docs": True,
            "loc": 100,
            "pinned_commit": True,
            "never_mvp": True,
        }
        s = score_candidate(c, quality_bar="never_MVP")
        self.assertTrue(s["accepted"])
        self.assertGreaterEqual(s["score"], 8)

    def test_mvp_hard_reject(self):
        c = {
            "has_tests": True,
            "has_ci": True,
            "has_schema": True,
            "loc": 50,
            "is_mvp": True,
        }
        s = score_candidate(c, quality_bar="never_MVP")
        self.assertFalse(s["accepted"])

    def test_select_best(self):
        cands = [
            {"has_tests": False, "loc": 50, "id": "weak"},
            {
                "has_tests": True,
                "has_ci": True,
                "has_schema": True,
                "pinned_commit": True,
                "loc": 80,
                "never_mvp": True,
                "id": "strong",
            },
        ]
        r = select_best(cands, quality_bar="never_MVP")
        self.assertEqual(r["reason"], "OK")
        self.assertEqual(r["selected"]["id"], "strong")

    def test_none_accepted(self):
        r = select_best([{"has_tests": False, "loc": 999}], quality_bar="never_MVP")
        self.assertIsNone(r["selected"])
        self.assertEqual(r["reason"], "NO_CANDIDATE_ACCEPTED")

    def test_standard_lower_threshold(self):
        c = {"has_tests": True, "has_schema": True, "loc": 100}
        s = score_candidate(c, quality_bar="standard")
        self.assertTrue(s["accepted"])


if __name__ == "__main__":
    unittest.main()
