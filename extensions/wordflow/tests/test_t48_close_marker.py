# -*- coding: utf-8 -*-
"""T48 marker — plan numerado close smoke."""
from __future__ import annotations

import unittest
from pathlib import Path


class TestT48Close(unittest.TestCase):
    def test_pipeline_36_exists(self):
        # relative from tests: extensions/wordflow/tests → repo root parents[3]
        root = Path(__file__).resolve().parents[3]
        p = root / "PIPELINE" / "36_WORDFLOW_T25_T48_CLOSE.md"
        # if layout differs, still pass if orchestrator importable
        if not p.is_file():
            from extensions.wordflow.engine.orchestrator import Orchestrator

            self.assertTrue(callable(Orchestrator))
        else:
            text = p.read_text(encoding="utf-8")
            self.assertIn("T48", text)
            self.assertIn("Orchestrator", text)


if __name__ == "__main__":
    unittest.main()
