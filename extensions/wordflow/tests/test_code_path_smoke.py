# -*- coding: utf-8 -*-
"""Tests C-31 code_path_smoke — offline integration, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.code_path_smoke import run_smoke


class TestCodePathSmoke(unittest.TestCase):
    def test_smoke(self):
        r = run_smoke()
        self.assertTrue(r["ok"], msg=str({k: v for k, v in r["steps"].items() if isinstance(v, dict) and not v.get("ok", True)}))
        self.assertEqual(r["llm_control"], "DENY")


if __name__ == "__main__":
    unittest.main()
