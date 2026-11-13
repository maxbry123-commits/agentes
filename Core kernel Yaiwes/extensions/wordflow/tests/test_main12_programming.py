# -*- coding: utf-8 -*-
"""FA-03 — main_12 yaml + programming_path. Offline."""
from __future__ import annotations

import unittest
from pathlib import Path

from extensions.wordflow.engine.programming_kwargs import minimal_block_kwargs


class TestMain12Yaml(unittest.TestCase):
    def test_load_main_12(self):
        try:
            import yaml  # noqa: F401
        except ImportError:
            self.skipTest("PyYAML missing")
        from extensions.wordflow.engine.main_loop import load_main_12
        cfg = load_main_12()
        self.assertEqual(cfg["loop_id"], "main_12")
        self.assertGreaterEqual(len(cfg["steps"]), 12)
        self.assertEqual(cfg["on_fail"], "stop")


class TestMain12Programming(unittest.TestCase):
    def test_programming_path_minimal(self):
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
            "block_id": "fa03-test",
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
        self.assertIn(state.get("status"), ("FAILED", "COMPLETED", "REJECTED", "RUNNING"))
        # FA-03: programming stage must appear when path enabled and council passed
        if state.get("status") == "FAILED" and state.get("stop_reason") == "PROGRAMMING_PATH_FAIL":
            self.assertIsNotNone(state.get("programming"))
            self.assertFalse(state["programming"].get("ok"))
            self.assertEqual(state["programming"].get("llm_control"), "DENY")
        elif state.get("programming") is not None:
            self.assertEqual(state["programming"].get("llm_control"), "DENY")


if __name__ == "__main__":
    unittest.main()
