# -*- coding: utf-8 -*-
"""Tests C-03 validator fail_closed — offline, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.validator import (
    ValidatorError,
    validate_architecture_output,
    validate_code_output,
)

ARCH_OK = {
    "schema_version": "1.0",
    "artifact_id": "arch.test",
    "files": [{"path": "a.py", "kind": "py"}],
    "evidence_ref": {"task_id": "C-03", "claim_status": "COMPLETED"},
}

CODE_OK = {
    "schema_version": "1.0",
    "artifact_id": "code.test",
    "language": "python",
    "files": [{"path": "b.py", "action": "create"}],
    "evidence_ref": {"task_id": "C-03", "claim_status": "COMPLETED"},
    "llm_control": "DENY",
}


class TestValidator(unittest.TestCase):
    def test_arch_ok(self):
        r = validate_architecture_output(ARCH_OK)
        self.assertTrue(r["ok"])

    def test_arch_missing_files_fail_closed(self):
        bad = dict(ARCH_OK)
        del bad["files"]
        with self.assertRaises(ValidatorError) as ctx:
            validate_architecture_output(bad, fail_closed=True)
        self.assertEqual(ctx.exception.reason_code, "ARCH_REJECTED")

    def test_arch_empty_files(self):
        bad = dict(ARCH_OK)
        bad["files"] = []
        with self.assertRaises(ValidatorError):
            validate_architecture_output(bad)

    def test_code_ok(self):
        r = validate_code_output(CODE_OK)
        self.assertTrue(r["ok"])

    def test_code_llm_not_deny(self):
        bad = dict(CODE_OK)
        bad["llm_control"] = "ALLOW"
        with self.assertRaises(ValidatorError) as ctx:
            validate_code_output(bad)
        self.assertIn("CODE_LLM_NOT_DENY", ctx.exception.detail)

    def test_code_missing_evidence_soft(self):
        bad = dict(CODE_OK)
        del bad["evidence_ref"]
        r = validate_code_output(bad, fail_closed=False)
        self.assertFalse(r["ok"])
        self.assertTrue(any("EVIDENCE" in x or "MISSING" in x for x in r["reason_codes"]))


if __name__ == "__main__":
    unittest.main()
