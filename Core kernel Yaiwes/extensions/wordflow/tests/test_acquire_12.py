# -*- coding: utf-8 -*-
"""Tests C-14 acquire_12 — offline, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.acquire_12 import AcquireError, acquire_12, parse_source


class TestAcquire12(unittest.TestCase):
    def test_parse_github(self):
        m = parse_source("https://github.com/maxbry123-commits/agentes")
        self.assertEqual(m["provider"], "github")
        self.assertEqual(m["name"], "agentes")

    def test_parse_hf(self):
        m = parse_source("hf://org/dataset")
        self.assertEqual(m["provider"], "hf")

    def test_plan_remote_blocked(self):
        r = acquire_12(["https://github.com/a/b", "local:///tmp/x"])
        self.assertTrue(r["ok"])
        self.assertGreaterEqual(r["remote_blocked"], 1)
        local = [i for i in r["items"] if i["provider"] == "local"][0]
        self.assertEqual(local["action"], "READY_TO_FETCH")

    def test_empty(self):
        with self.assertRaises(AcquireError):
            acquire_12([])


if __name__ == "__main__":
    unittest.main()
