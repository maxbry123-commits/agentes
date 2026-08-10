# -*- coding: utf-8 -*-
"""A-SE-03 tests — license gate + install planner."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from source_evolution.engine.install_planner import build_install_plan  # noqa: E402
from source_evolution.engine.license_gate import check_license, load_licenses  # noqa: E402

LIC = Path(__file__).resolve().parents[1] / "store" / "licenses.yaml"


def _pin(license="MIT", **kw):
    b = {
        "schema_version": "1.0",
        "pin_id": "pin-lic-1",
        "source_type": "git",
        "locator": {"uri": "https://github.com/x/y.git"},
        "digest": {
            "algo": "git_commit",
            "value": "abcdef0123456789abcdef0123456789abcdef01",
        },
        "license": license,
    }
    b.update(kw)
    return b


class TestLicenseInstall(unittest.TestCase):
    def test_load_table(self):
        cfg = load_licenses(LIC)
        self.assertIn("MIT", cfg["licenses"])
        self.assertEqual(cfg["licenses"]["GPL-3.0"]["verdict"], "STOP")

    def test_pass_mit(self):
        r = check_license("MIT", LIC)
        self.assertTrue(r["allowed"])
        self.assertEqual(r["verdict"], "PASS")

    def test_stop_gpl(self):
        r = check_license("GPL-3.0", LIC)
        self.assertTrue(r["blocked"])

    def test_director_mpl(self):
        r = check_license("MPL-2.0", LIC)
        self.assertTrue(r["needs_director"])

    def test_install_blocked_license(self):
        plan = build_install_plan(_pin(license="GPL-3.0"))
        self.assertEqual(plan["status"], "BLOCKED")
        self.assertEqual(plan["reason"], "LICENSE_STOP")

    def test_install_needs_director(self):
        plan = build_install_plan(_pin(license="MPL-2.0"))
        self.assertEqual(plan["status"], "NEEDS_DIRECTOR")

    def test_install_planned(self):
        fetch = {"status": "SUCCESS", "artifact_dir": "artifacts/sources/pin-lic-1"}
        plan = build_install_plan(_pin(license="MIT"), fetch_result=fetch)
        self.assertEqual(plan["status"], "PLANNED")
        ops = [s["op"] for s in plan["steps"]]
        self.assertIn("copy_tree", ops)
        self.assertIn("write_provenance", ops)

    def test_install_fetch_failed(self):
        plan = build_install_plan(
            _pin(license="MIT"), fetch_result={"status": "FAILED"}
        )
        self.assertEqual(plan["status"], "BLOCKED")
        self.assertEqual(plan["reason"], "FETCH_NOT_SUCCESS")


if __name__ == "__main__":
    unittest.main()
