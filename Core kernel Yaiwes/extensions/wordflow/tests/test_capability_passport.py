# -*- coding: utf-8 -*-
"""Tests T11 CapabilityPassport."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.capability_passport import (
    authorize,
    default_engine_passport,
    issue_passport,
    verify_passport,
)


class TestCapabilityPassport(unittest.TestCase):
    def test_issue_verify(self):
        p = issue_passport(
            subject_id="fake_static",
            subject_kind="engine",
            capabilities=["route:ANALYSIS", "resource:read"],
            denied=["bus:bypass"],
        )
        self.assertTrue(verify_passport(p)["ok"])

    def test_authorize_allow_deny(self):
        p = default_engine_passport("fake_static")
        self.assertTrue(authorize(p, "route:ANALYSIS")["ok"])
        self.assertFalse(authorize(p, "bus:bypass")["ok"])
        self.assertFalse(authorize(p, "resource:fetch_remote")["ok"])

    def test_prefix(self):
        p = issue_passport(
            subject_id="x",
            subject_kind="tool",
            capabilities=["resource:*"],
        )
        self.assertTrue(authorize(p, "resource:read")["ok"])

    def test_revoked(self):
        p = issue_passport(
            subject_id="x",
            subject_kind="agent",
            capabilities=["route:ANALYSIS"],
            status="REVOKED",
        )
        self.assertFalse(verify_passport(p)["ok"])

    def test_tamper(self):
        p = default_engine_passport("e1")
        p["capabilities"] = list(p["capabilities"]) + ["bus:bypass"]
        self.assertFalse(verify_passport(p)["ok"])


if __name__ == "__main__":
    unittest.main()
