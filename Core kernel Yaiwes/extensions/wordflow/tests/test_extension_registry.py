# -*- coding: utf-8 -*-
"""Tests T38 ExtensionRegistry."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.extension_registry import ExtensionRegistry


class TestExtensionRegistry(unittest.TestCase):
    def test_register_load(self):
        reg = ExtensionRegistry()
        reg.register(
            "pkg.publisher",
            kind="capability",
            capabilities=["github_publish"],
            factory=lambda: {"name": "pub"},
        )
        r = reg.load("pkg.publisher")
        self.assertTrue(r["ok"])
        self.assertEqual(r["instance"]["name"], "pub")

    def test_find_cap(self):
        reg = ExtensionRegistry()
        reg.register("a", kind="tool", capabilities=["search"])
        self.assertEqual(reg.find_by_capability("search"), ["a"])

    def test_duplicate(self):
        reg = ExtensionRegistry()
        reg.register("x", kind="x")
        with self.assertRaises(ValueError):
            reg.register("x", kind="x")


if __name__ == "__main__":
    unittest.main()
