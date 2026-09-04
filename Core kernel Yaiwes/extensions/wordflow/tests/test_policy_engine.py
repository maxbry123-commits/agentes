# -*- coding: utf-8 -*-
"""Tests C-26 Policy Engine — offline, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.policy_engine import (
    PolicyError,
    check_action,
    load_policy,
    require_allowed,
)


class TestPolicyEngine(unittest.TestCase):
    def setUp(self):
        self.p = load_policy()

    def test_deny_write_kernel(self):
        r = check_action(self.p, "write_kernel")
        self.assertFalse(r["allowed"])
        self.assertIn("DENY_WRITE_KERNEL", r["reason_codes"])

    def test_deny_github_until_authorized(self):
        r = check_action(self.p, "deploy", expected_head="abc")
        self.assertFalse(r["allowed"])

    def test_license_gate(self):
        r = check_action(self.p, "use_license", license="MIT")
        self.assertTrue(r["allowed"])
        r2 = check_action(self.p, "use_license", license="Proprietary")
        self.assertFalse(r2["allowed"])

    def test_no_literal_token(self):
        r = check_action(self.p, "use_credential", literal_token="ghp_x", provider="github")
        self.assertFalse(r["allowed"])

    def test_require_raises(self):
        with self.assertRaises(PolicyError):
            require_allowed(self.p, "write_kernel")

    def test_llm_deny_marker(self):
        r = check_action(self.p, "use_license", license="MIT")
        self.assertEqual(r["llm_control"], "DENY")


if __name__ == "__main__":
    unittest.main()
