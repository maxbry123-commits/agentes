# -*- coding: utf-8 -*-
"""Tests T35 HFResourceIndex."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.hf_index import HFResourceIndex, make_hf_entry


class TestHFIndex(unittest.TestCase):
    def test_register_find(self):
        idx = HFResourceIndex()
        e = make_hf_entry(kind="skill", hf_id="org/skill-x", fetchable=False)
        idx.register(e)
        found = idx.find(kind="skill")
        self.assertEqual(len(found), 1)

    def test_fetch_disabled(self):
        idx = HFResourceIndex()
        e = make_hf_entry(kind="dataset", hf_id="org/ds", fetchable=False)
        idx.register(e)
        r = idx.request_fetch(e["resource_id"])
        self.assertEqual(r["reason"], "FETCH_DISABLED")

    def test_fetch_planned(self):
        idx = HFResourceIndex()
        e = make_hf_entry(kind="adapter", hf_id="org/ad", fetchable=True)
        idx.register(e)
        r = idx.request_fetch(e["resource_id"])
        self.assertTrue(r["ok"])
        self.assertEqual(r["action"], "FETCH_PLANNED")


if __name__ == "__main__":
    unittest.main()
