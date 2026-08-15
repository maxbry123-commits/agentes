# -*- coding: utf-8 -*-
"""Tests C-19 code_path_runner — offline, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.code_path_runner import run_code_path

TEXT = (
    "Objetivo: implementar runner del path de code determinista "
    "con quality bar y evidence packet para Wordflow."
)


class TestCodePathRunner(unittest.TestCase):
    def test_happy(self):
        r = run_code_path(TEXT, mission_id="m19")
        self.assertTrue(r["ok"])
        self.assertTrue(r["evidence_ok"])
        self.assertEqual(r["llm_control"], "DENY")

    def test_with_skill(self):
        r = run_code_path(TEXT, skill={"package_id": "sk.path"})
        self.assertTrue(r["skill_compile"]["ok"])

    def test_reject_short(self):
        r = run_code_path("x")
        self.assertFalse(r["ok"])
        self.assertEqual(r["stage"], "quality_bar")


if __name__ == "__main__":
    unittest.main()
