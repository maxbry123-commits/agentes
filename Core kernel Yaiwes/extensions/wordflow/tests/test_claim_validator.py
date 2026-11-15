# -*- coding: utf-8 -*-
"""Tests C-22 claim_validator — offline, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.claim_validator import ClaimError, require_claim, validate_claim


class TestClaimValidator(unittest.TestCase):
    def test_partial_ok(self):
        r = validate_claim({"task_id": "C-22", "claim_status": "PARTIAL"})
        self.assertTrue(r["ok"])

    def test_completed_requires_evidence(self):
        r = validate_claim({"task_id": "C-22", "claim_status": "COMPLETED"})
        self.assertFalse(r["ok"])
        self.assertIn("PATHS_REQUIRED", r["reason_codes"])

    def test_completed_full(self):
        r = validate_claim({
            "task_id": "C-22",
            "claim_status": "COMPLETED",
            "paths": [{"path": "a.py", "blob_sha": "abc"}],
            "tests": {"passed": 1},
            "doc_anchors": ["C-22"],
        })
        self.assertTrue(r["ok"])

    def test_require_raises(self):
        with self.assertRaises(ClaimError):
            require_claim({"claim_status": "COMPLETED"})


if __name__ == "__main__":
    unittest.main()
