# -*- coding: utf-8 -*-
"""Tests C-15 reuse_12 — offline, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.resource_catalog import ResourceCatalog, make_entry
from extensions.wordflow.engine.reuse_12 import reuse_12


class TestReuse12(unittest.TestCase):
    def setUp(self):
        self.cat = ResourceCatalog()
        self.cat.add(make_entry(name="auth-skill", kind="skill", source="local", tags=["auth"]))

    def test_reuse_hit(self):
        r = reuse_12(self.cat, "auth-skill", kind="skill")
        self.assertEqual(r["action"], "REUSE")

    def test_generate_miss(self):
        r = reuse_12(self.cat, "totally-new-thing")
        self.assertEqual(r["action"], "GENERATE")


if __name__ == "__main__":
    unittest.main()
