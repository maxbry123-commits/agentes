# -*- coding: utf-8 -*-
"""A-WF-03 tests — refute L1-L3 + repair R1-R6."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wordflow.engine.goals_extractor import extract_goals_in  # noqa: E402
from wordflow.engine.input_normalizer import normalize_input_block  # noqa: E402
from wordflow.engine.refute_repair import (  # noqa: E402
    apply_auto_repairs,
    propose_repairs,
    refute_block,
)


def _ok_block(**kw):
    b = {
        "schema_version": "1.0",
        "block_id": "IB-R1",
        "source_type": "chat",
        "raw_text": "Implementar fingerprint en control-layer ≤120 LOC",
        "quality_bar": "never_MVP",
        "goals_hint": ["fingerprint"],
        "priority": "P0",
        "constraints": {"loc_limit": 120, "success_criteria": "tests green"},
    }
    b.update(kw)
    return normalize_input_block(b)


class TestRefuteRepair(unittest.TestCase):
    def test_pass_clean(self):
        block = _ok_block()
        goals = extract_goals_in(block)
        r = refute_block(block, goals)
        self.assertTrue(r["pass"])
        self.assertEqual(r["count"], 0)

    def test_l2_no_success_never_mvp(self):
        block = _ok_block(constraints={"loc_limit": 100})
        goals = extract_goals_in(block)
        r = refute_block(block, goals)
        self.assertFalse(r["pass"])
        self.assertIn("L2_NO_SUCCESS_CRITERIA", r["codes"])

    def test_l3_budget(self):
        block = _ok_block(constraints={"loc_limit": 500, "success_criteria": "ok"})
        goals = extract_goals_in(block)
        r = refute_block(block, goals)
        self.assertIn("L3_BUDGET_EXCEEDED", r["codes"])
        self.assertEqual(r["worst_layer"], "L3")

    def test_propose_r4_on_budget(self):
        block = _ok_block(constraints={"loc_limit": 500, "success_criteria": "ok"})
        goals = extract_goals_in(block)
        r = refute_block(block, goals)
        props = propose_repairs(r, block)
        actions = [p["action"] for p in props]
        self.assertIn("R4_DOWNGRADE_PRIORITY", actions)

    def test_apply_auto_r4(self):
        block = _ok_block(constraints={"loc_limit": 500, "success_criteria": "ok"})
        goals = extract_goals_in(block)
        r = refute_block(block, goals)
        props = propose_repairs(r, block)
        new_b, applied = apply_auto_repairs(block, props)
        self.assertIn("R4_DOWNGRADE_PRIORITY", applied)
        self.assertEqual(new_b["priority"], "P3")

    def test_cap_respected(self):
        block = _ok_block(constraints={"loc_limit": 500, "success_criteria": "ok"})
        goals = extract_goals_in(block)
        r = refute_block(block, goals)
        props = propose_repairs(r, block, applied_counts={"R4_DOWNGRADE_PRIORITY": 1})
        actions = [p["action"] for p in props]
        self.assertNotIn("R4_DOWNGRADE_PRIORITY", actions)

    def test_reject_on_empty(self):
        block = {
            "schema_version": "1.0",
            "block_id": "X",
            "source_type": "chat",
            "raw_text": "",
            "quality_bar": "standard",
            "goals_hint": [],
            "priority": "P1",
            "flags": {},
            "constraints": {},
            "meta": {},
        }
        r = refute_block(block, {})
        self.assertIn("L1_EMPTY_TEXT", r["codes"])
        props = propose_repairs(r, block)
        self.assertTrue(any(p["action"] == "R6_REJECT_BLOCK" for p in props))


if __name__ == "__main__":
    unittest.main()
