# -*- coding: utf-8 -*-
"""A-WF-02 tests — goals catalog + extractor."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wordflow.engine.goals_extractor import (  # noqa: E402
    empty_goals_out,
    extract_goals_in,
    load_goals_catalog,
)
from wordflow.engine.input_normalizer import normalize_input_block  # noqa: E402

CATALOG = Path(__file__).resolve().parents[1] / "store" / "goals_catalog.yaml"


def _block(**kw):
    b = {
        "schema_version": "1.0",
        "block_id": "IB-G1",
        "source_type": "chat",
        "raw_text": (
            "Implementar control-layer/control/fingerprint.py "
            "≤120 LOC never_MVP en fase control-layer"
        ),
        "quality_bar": "never_MVP",
        "goals_hint": ["fingerprint", "tests"],
        "priority": "P0",
        "doc_refs": [{"doc_id": "SALIDA4_FP", "section": "§14.2"}],
        "constraints": {"loc_limit": 120, "success_criteria": "tests pass"},
    }
    b.update(kw)
    return normalize_input_block(b)


class TestGoals(unittest.TestCase):
    def test_catalog_12_12(self):
        cat = load_goals_catalog(CATALOG)
        self.assertEqual(len(cat["goals_in"]), 12)
        self.assertEqual(len(cat["goals_out"]), 12)

    def test_extract_basic(self):
        g = extract_goals_in(_block())
        self.assertEqual(g["total_in"], 12)
        self.assertGreaterEqual(g["covered_count"], 8)
        self.assertTrue(g["never_mvp"])
        self.assertEqual(g["resolved"]["GIN-03"]["value"], "never_MVP")
        self.assertEqual(g["resolved"]["GIN-05"]["value"], "P0")

    def test_extract_paths(self):
        g = extract_goals_in(_block())
        paths = g["resolved"]["GIN-08"]["value"]
        self.assertTrue(any("fingerprint.py" in p for p in paths))

    def test_extract_phase(self):
        g = extract_goals_in(_block())
        phase = g["resolved"]["GIN-09"]["value"]
        self.assertIsNotNone(phase)
        self.assertIn("control-layer", phase)

    def test_extract_repair(self):
        b = _block(source_type="repair", parent_block_id="IB-0")
        g = extract_goals_in(b)
        self.assertTrue(g["resolved"]["GIN-06"]["value"]["is_repair"])

    def test_empty_goals_out(self):
        out = empty_goals_out()
        self.assertEqual(len(out), 12)
        self.assertEqual(out["GOUT-01"]["status"], "PENDING")

    def test_loc_budget(self):
        g = extract_goals_in(_block())
        budget = g["resolved"]["GIN-11"]["value"]
        self.assertEqual(budget["loc_limit"], 120)


if __name__ == "__main__":
    unittest.main()
