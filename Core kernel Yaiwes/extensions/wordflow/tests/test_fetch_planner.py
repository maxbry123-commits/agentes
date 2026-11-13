# -*- coding: utf-8 -*-
"""Tests D3 FetchPlanner."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.fetch_planner import FetchPlanner
from extensions.wordflow.engine.hf_index import HFResourceIndex, make_hf_entry


class TestFetchPlanner(unittest.TestCase):
    def test_blocked_by_default(self):
        idx = HFResourceIndex()
        e = make_hf_entry(kind="skill", hf_id="org/s", fetchable=True)
        idx.register(e)
        fp = FetchPlanner(hf_index=idx)
        r = fp.plan_hf(e["resource_id"])
        self.assertEqual(r["action"], "FETCH_BLOCKED")

    def test_ready_when_enabled(self):
        idx = HFResourceIndex()
        e = make_hf_entry(kind="skill", hf_id="org/s", fetchable=True)
        idx.register(e)
        fp = FetchPlanner(hf_index=idx, allow_fetch=True)
        r = fp.plan_hf(e["resource_id"])
        self.assertEqual(r["action"], "FETCH_READY")

    def test_checksum(self):
        fp = FetchPlanner()
        h = fp.verify_checksum("abc", fp.verify_checksum("abc", "x")["got"])
        # second call with correct expected
        got = fp.verify_checksum("abc", "x")["got"]
        self.assertTrue(fp.verify_checksum("abc", got)["ok"])


if __name__ == "__main__":
    unittest.main()
