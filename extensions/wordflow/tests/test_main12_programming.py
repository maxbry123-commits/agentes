# -*- coding: utf-8 -*-
"""U9 — main_12 + programming_path smoke. Offline."""
from __future__ import annotations

import unittest
from pathlib import Path

from extensions.wordflow.engine.programming_kwargs import minimal_block_kwargs


class TestMain12Programming(unittest.TestCase):
    def test_programming_path_minimal_or_skip(self):
        yaml_path = Path(__file__).resolve().parents[1] / "store" / "main_12.yaml"
        if not yaml_path.exists():
            self.skipTest("main_12.yaml missing")
        try:
            import yaml  # noqa: F401
        except ImportError:
            self.skipTest("PyYAML missing")

        from extensions.wordflow.engine.main_loop import run_main_12

        raw = {
            "schema_version": "1.0",
            "block_id": "u9-test",
            "source_type": "test",
            "raw_text": "Objetivo: validar programming_path minimal en main_12 Wordflow code path determinista.",
            "quality_bar": {},
            "goals_hint": ["wire programming"],
            "priority": "P1",
            "doc_refs": [],
            "constraints": [],
            "meta": {},
        }
        state = run_main_12(
            raw,
            programming_path=True,
            programming_kwargs=minimal_block_kwargs(),
            programming_full_pass=False,
        )
        # minimal → forensic FAIL expected; loop may FAILED or COMPLETED depending on on_fail
        self.assertIn(state.get("status"), ("FAILED", "COMPLETED", "REJECTED", "RUNNING"))
        if state.get("programming") is not None:
            self.assertFalse(state["programming"].get("ok"))
            self.assertEqual(state["programming"].get("llm_control"), "DENY")


if __name__ == "__main__":
    unittest.main()
