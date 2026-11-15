# -*- coding: utf-8 -*-
"""A-WF-07 tests — wordflow entrypoint."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wordflow.engine.entrypoint import run_wordflow  # noqa: E402


def _raw(**kw):
    b = {
        "schema_version": "1.0",
        "block_id": "IB-E1",
        "source_type": "chat",
        "raw_text": "Implementar fingerprint control-layer ≤120 LOC",
        "quality_bar": "never_MVP",
        "goals_hint": ["fingerprint"],
        "priority": "P0",
        "doc_refs": [{"doc_id": "SALIDA4_FP"}],
        "constraints": {"loc_limit": 120, "success_criteria": "ok"},
    }
    b.update(kw)
    return b


class TestWFEntrypoint(unittest.TestCase):
    def test_ok(self):
        r = run_wordflow(_raw())
        self.assertTrue(r["ok"])
        self.assertEqual(r["status"], "COMPLETED")
        self.assertEqual(r["council"], "APPROVE")
        self.assertEqual(r["sentinel"], "PASS")
        self.assertGreater(len(r["tasks"]), 0)

    def test_fail_none(self):
        r = run_wordflow(None)
        self.assertFalse(r["ok"])
        self.assertEqual(r["status"], "FAILED")

    def test_compact_keys(self):
        r = run_wordflow(_raw())
        for k in (
            "ok",
            "status",
            "block_id",
            "tasks",
            "council",
            "sentinel",
            "checkpoint",
        ):
            self.assertIn(k, r)


if __name__ == "__main__":
    unittest.main()
