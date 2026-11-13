# -*- coding: utf-8 -*-
"""A-SE-02 tests — fetch planner + FakeFetcher."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from source_evolution.engine.fetch_planner import (  # noqa: E402
    FakeFetcher,
    build_fetch_plan,
)
from source_evolution.engine.version_pin import VersionPinError  # noqa: E402


def _git_pin(**kw):
    b = {
        "schema_version": "1.0",
        "pin_id": "pin-git-1",
        "source_type": "git",
        "locator": {"uri": "https://github.com/example/repo.git", "ref": "v1.0"},
        "digest": {
            "algo": "git_commit",
            "value": "abcdef0123456789abcdef0123456789abcdef01",
        },
    }
    b.update(kw)
    return b


class TestFetchPlanner(unittest.TestCase):
    def test_git_plan(self):
        plan = build_fetch_plan(_git_pin())
        self.assertEqual(plan["status"], "PLANNED")
        ops = [s["op"] for s in plan["steps"]]
        self.assertIn("git_clone", ops)
        self.assertIn("verify_commit", ops)
        self.assertEqual(plan["llm_control"], "DENY")

    def test_hf_plan(self):
        pin = _git_pin(
            pin_id="pin-hf",
            source_type="hf",
            locator={"uri": "org/model", "ref": "main"},
            digest={"algo": "sha256", "value": "a" * 64},
        )
        plan = build_fetch_plan(pin)
        self.assertEqual(plan["steps"][0]["op"], "hf_download")

    def test_package_plan(self):
        pin = _git_pin(
            pin_id="pin-pkg",
            source_type="package",
            locator={"uri": "requests", "package_name": "requests", "version": "2.31.0"},
            digest={"algo": "sha256", "value": "b" * 64},
        )
        plan = build_fetch_plan(pin)
        self.assertEqual(plan["steps"][0]["op"], "package_download")

    def test_invalid_pin(self):
        with self.assertRaises(VersionPinError):
            build_fetch_plan(None)

    def test_fake_execute_ok(self):
        fetcher = FakeFetcher()
        plan = fetcher.plan(_git_pin())
        result = fetcher.execute(plan)
        self.assertEqual(result["status"], "SUCCESS")
        self.assertTrue(all(s["status"] == "OK" for s in result["steps"]))

    def test_fake_execute_fail(self):
        fetcher = FakeFetcher(fail_on="verify_commit")
        plan = fetcher.plan(_git_pin())
        result = fetcher.execute(plan)
        self.assertEqual(result["status"], "FAILED")


if __name__ == "__main__":
    unittest.main()
