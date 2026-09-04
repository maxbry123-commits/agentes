# -*- coding: utf-8 -*-
"""A-SE-04 tests — run_acquire entrypoint."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from source_evolution.engine.entrypoint import run_acquire  # noqa: E402
from source_evolution.engine.fetch_planner import FakeFetcher  # noqa: E402


def _pin(license="MIT", **kw):
    b = {
        "schema_version": "1.0",
        "pin_id": "pin-acq-1",
        "source_type": "git",
        "locator": {"uri": "https://github.com/x/y.git", "ref": "main"},
        "digest": {
            "algo": "git_commit",
            "value": "abcdef0123456789abcdef0123456789abcdef01",
        },
        "license": license,
    }
    b.update(kw)
    return b


class TestSEEntrypoint(unittest.TestCase):
    def test_ok(self):
        r = run_acquire(_pin(), fetcher=FakeFetcher())
        self.assertTrue(r["ok"])
        self.assertEqual(r["status"], "COMPLETED")
        self.assertEqual(r["license_verdict"], "PASS")
        self.assertEqual(r["fetch_result"]["status"], "SUCCESS")

    def test_gpl_blocked(self):
        r = run_acquire(_pin(license="GPL-3.0"), fetcher=FakeFetcher())
        self.assertFalse(r["ok"])
        self.assertEqual(r["status"], "BLOCKED")

    def test_fetch_fail(self):
        r = run_acquire(_pin(), fetcher=FakeFetcher(fail_on="git_clone"))
        self.assertFalse(r["ok"])
        self.assertEqual(r["status"], "FAILED")

    def test_plan_only(self):
        r = run_acquire(_pin(), execute=False)
        self.assertTrue(r["ok"])
        self.assertEqual(r["fetch_result"]["status"], "SKIPPED")

    def test_bad_pin(self):
        r = run_acquire(None)
        self.assertFalse(r["ok"])
        self.assertEqual(r["reason"], "MISSING_PIN")


if __name__ == "__main__":
    unittest.main()
