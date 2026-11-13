# -*- coding: utf-8 -*-
"""Tests C-04 dual_compiler — offline, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.dual_compiler import (
    DualCompilerError,
    check_version_pin,
    compile_output,
    promote_12,
)

ARCH = {
    "schema_version": "1.0",
    "artifact_id": "a1",
    "files": [{"path": "x.yaml", "kind": "yaml"}],
    "evidence_ref": {"task_id": "C-04", "claim_status": "COMPLETED"},
}
CODE = {
    "schema_version": "1.0",
    "artifact_id": "c1",
    "language": "python",
    "files": [{"path": "y.py", "action": "create"}],
    "evidence_ref": {"task_id": "C-04", "claim_status": "COMPLETED"},
    "llm_control": "DENY",
}
PIN = "a" * 40


class TestDualCompiler(unittest.TestCase):
    def test_pin_ok(self):
        self.assertTrue(check_version_pin(PIN)["ok"])
        self.assertFalse(check_version_pin("short")["ok"])

    def test_compile_arch(self):
        r = compile_output("knowledge", ARCH, version_pin=PIN, require_pin=True)
        self.assertTrue(r["ok"])
        self.assertEqual(r["track"], "knowledge")

    def test_compile_code(self):
        r = compile_output("code", CODE)
        self.assertEqual(r["track"], "code")

    def test_compile_bad_raises(self):
        with self.assertRaises(DualCompilerError):
            compile_output("code", {"artifact_id": "x"})

    def test_promote(self):
        p = promote_12(package_id="pkg.1", track="code", version_pin=PIN)
        self.assertTrue(p["ok"])
        self.assertEqual(p["status"], "AVAILABLE")

    def test_promote_bad_pin(self):
        p = promote_12(package_id="pkg.1", track="code", version_pin="no")
        self.assertFalse(p["ok"])


if __name__ == "__main__":
    unittest.main()
