# -*- coding: utf-8 -*-
"""A-WF-06 tests — main_12 loop runner."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wordflow.engine.main_loop import load_main_12, run_main_12  # noqa: E402

LOOP = Path(__file__).resolve().parents[1] / "store" / "main_12.yaml"


def _raw(**kw):
    b = {
        "schema_version": "1.0",
        "block_id": "IB-M1",
        "source_type": "chat",
        "raw_text": "Implementar control-layer/control/fingerprint.py ≤120 LOC",
        "quality_bar": "never_MVP",
        "goals_hint": ["fingerprint", "tests"],
        "priority": "P0",
        "doc_refs": [{"doc_id": "SALIDA4_FP", "section": "§14.2"}],
        "constraints": {"loc_limit": 120, "success_criteria": "tests green"},
    }
    b.update(kw)
    return b


class TestMainLoop(unittest.TestCase):
    def test_load_12_steps(self):
        cfg = load_main_12(LOOP)
        self.assertEqual(cfg["loop_id"], "main_12")
        self.assertEqual(len(cfg["steps"]), 12)

    def test_completed_happy(self):
        state = run_main_12(_raw(), loop_path=LOOP)
        self.assertEqual(state["status"], "COMPLETED")
        self.assertEqual(len(state["step_results"]), 12)
        self.assertTrue(all(s["ok"] for s in state["step_results"]))
        self.assertGreater(len(state["tasks"]), 0)

    def test_fail_on_bad_schema(self):
        state = run_main_12(None, loop_path=LOOP)
        self.assertEqual(state["status"], "FAILED")
        self.assertEqual(state["stop_reason"], "MISSING_BLOCK")

    def test_fail_sentinel_budget(self):
        state = run_main_12(
            _raw(constraints={"loc_limit": 500, "success_criteria": "ok"}),
            loop_path=LOOP,
        )
        self.assertIn(state["status"], ("FAILED", "REJECTED"))
        self.assertIsNotNone(state["stop_reason"])

    def test_goals_out_filled(self):
        state = run_main_12(_raw(), loop_path=LOOP)
        done = [
            k for k, v in state["goals_out"].items() if v.get("status") == "DONE"
        ]
        self.assertGreaterEqual(len(done), 6)

    def test_council_present(self):
        state = run_main_12(_raw(), loop_path=LOOP)
        self.assertIsNotNone(state.get("council"))
        self.assertEqual(state["council"]["decision"], "APPROVE")


if __name__ == "__main__":
    unittest.main()
