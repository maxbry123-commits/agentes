# -*- coding: utf-8 -*-
"""Tests T41 WordflowBootstrap."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.bootstrap import WordflowKernel


class TestBootstrap(unittest.TestCase):
    def test_start(self):
        k = WordflowKernel()
        r = k.start()
        self.assertTrue(r["ok"])
        self.assertGreaterEqual(len(r["packages"]), 3)

    def test_load_publisher(self):
        k = WordflowKernel()
        k.start()
        r = k.load("wordflow.github_publisher")
        self.assertTrue(r["ok"])
        self.assertIsNotNone(r["instance"])

    def test_load_before_start(self):
        k = WordflowKernel()
        r = k.load("wordflow.runtime_bus")
        self.assertEqual(r["reason"], "NOT_STARTED")


if __name__ == "__main__":
    unittest.main()
