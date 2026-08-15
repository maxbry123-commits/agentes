# -*- coding: utf-8 -*-
"""Tests C-29 hf_resolver — offline, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.hf_resolver import HFResolverError, batch_resolve, resolve_hf_ref


class TestHFResolver(unittest.TestCase):
    def test_plan_only(self):
        r = resolve_hf_ref("hf://org/skill-pack", kind="skill")
        self.assertTrue(r["ok"])
        self.assertEqual(r["action"], "PLAN_ONLY")
        self.assertEqual(r["llm_control"], "DENY")

    def test_batch(self):
        b = batch_resolve(["hf://a/b", "hf://c/d"])
        self.assertEqual(b["count"], 2)

    def test_empty(self):
        with self.assertRaises(HFResolverError):
            resolve_hf_ref("")


if __name__ == "__main__":
    unittest.main()
