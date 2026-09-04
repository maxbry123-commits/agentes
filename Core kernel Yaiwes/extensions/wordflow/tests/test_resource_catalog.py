# -*- coding: utf-8 -*-
"""Tests T9 ResourceCatalog."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from extensions.wordflow.engine.resource_catalog import (
    ResourceCatalog,
    make_entry,
    seed_hf_index_stub,
    verify_entry,
)


class TestResourceCatalog(unittest.TestCase):
    def test_local_entry(self):
        e = make_entry(name="local-skill", kind="skill", source="local", fetchable=True)
        self.assertTrue(verify_entry(e)["ok"])
        self.assertTrue(e["fetchable"])

    def test_hf_not_fetchable(self):
        e = make_entry(name="x", kind="dataset", source="hf", ref="hf://x")
        self.assertFalse(e["fetchable"])
        with self.assertRaises(ValueError):
            make_entry(name="y", kind="skill", source="hf", fetchable=True)

    def test_catalog_filter(self):
        cat = ResourceCatalog()
        for e in seed_hf_index_stub():
            cat.add(e)
        cat.add(make_entry(name="local-tool", kind="tool", source="local", tags=["dev"]))
        self.assertEqual(len(cat.list(source="hf")), 3)
        self.assertEqual(len(cat.list(kind="tool")), 1)
        self.assertTrue(cat.search_name("example-skill"))

    def test_persist(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "index.json"
            c1 = ResourceCatalog(path)
            c1.add(make_entry(name="a", kind="other", source="local"))
            c1.save()
            c2 = ResourceCatalog(path)
            self.assertEqual(len(c2.list()), 1)


if __name__ == "__main__":
    unittest.main()
