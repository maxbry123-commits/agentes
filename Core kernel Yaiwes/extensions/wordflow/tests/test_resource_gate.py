# -*- coding: utf-8 -*-
"""Tests T10 ResourceGate."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.resource_catalog import ResourceCatalog, make_entry
from extensions.wordflow.engine.resource_gate import check_entry, gate_catalog_get


class TestResourceGate(unittest.TestCase):
    def test_read_ok(self):
        e = make_entry(name="s", kind="skill", source="hf", ref="hf://x")
        r = check_entry(e, action="read")
        self.assertTrue(r["ok"])

    def test_fetch_hf_denied(self):
        e = make_entry(name="s", kind="skill", source="hf", ref="hf://x")
        r = check_entry(e, action="fetch")
        self.assertFalse(r["ok"])
        self.assertEqual(r["reason"], "REMOTE_FETCH_DENIED_PRE_POST_WORDFLOW")

    def test_fetch_local_ok(self):
        e = make_entry(name="s", kind="skill", source="local", fetchable=True)
        r = check_entry(e, action="fetch")
        self.assertTrue(r["ok"])

    def test_prepare_ok_even_remote(self):
        e = make_entry(name="s", kind="dataset", source="hf", ref="hf://d")
        r = check_entry(e, action="prepare")
        self.assertTrue(r["ok"])

    def test_gate_catalog(self):
        cat = ResourceCatalog()
        e = make_entry(name="t", kind="tool", source="local", fetchable=True)
        cat.add(e)
        r = gate_catalog_get(cat, e["resource_id"], action="fetch")
        self.assertTrue(r["ok"])
        missing = gate_catalog_get(cat, "nope", action="read")
        self.assertEqual(missing["reason"], "NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
