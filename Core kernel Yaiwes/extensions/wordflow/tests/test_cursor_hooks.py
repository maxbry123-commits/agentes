# -*- coding: utf-8 -*-
"""A-WF-10 tests — cursor techniques hooks."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wordflow.engine.cursor_hooks import (  # noqa: E402
    apply_hooks,
    load_techniques,
    techniques_for_hook,
)

CAT = Path(__file__).resolve().parents[1] / "store" / "cursor_techniques.yaml"


class TestCursorHooks(unittest.TestCase):
    def test_load_10(self):
        techs = load_techniques(CAT)
        self.assertEqual(len(techs), 10)

    def test_hook_filter(self):
        before_write = techniques_for_hook("before_write", CAT)
        self.assertTrue(any(t["id"] == "CT-04" for t in before_write))

    def test_loc_violation(self):
        r = apply_hooks("before_write", {"loc": 500}, CAT)
        self.assertFalse(r["ok"])
        self.assertTrue(any(v["reason"] == "LOC_CAP" for v in r["violations"]))

    def test_never_mvp_ok(self):
        r = apply_hooks(
            "on_sentinel",
            {"quality_bar": "never_MVP", "success_criteria": "tests"},
            CAT,
        )
        self.assertTrue(r["ok"])

    def test_never_mvp_fail(self):
        r = apply_hooks(
            "on_sentinel",
            {"quality_bar": "never_MVP"},
            CAT,
        )
        self.assertFalse(r["ok"])


if __name__ == "__main__":
    unittest.main()
