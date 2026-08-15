# -*- coding: utf-8 -*-
"""Tests C-02 enchufe_gate — offline, 0% LLM."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from extensions.wordflow.engine.enchufe_gate import (
    EnchufeGateError,
    gate_load,
    validate_ficha,
)

VALID = {
    "artifact_id": "test.module",
    "abi_version": "2.0",
    "extension_type": "runtime",
    "kernel_min": "0.1.0",
    "mount_mode": "sidecar",
    "load_priority": 10,
    "llm_control": "DENY",
}


class TestEnchufeGate(unittest.TestCase):
    def test_validate_ok(self):
        r = validate_ficha(dict(VALID))
        self.assertTrue(r["ok"])
        self.assertEqual(r["reason_codes"], [])

    def test_missing_field(self):
        bad = dict(VALID)
        del bad["artifact_id"]
        r = validate_ficha(bad)
        self.assertFalse(r["ok"])
        self.assertIn("MISSING_artifact_id", r["reason_codes"])

    def test_llm_not_deny(self):
        bad = dict(VALID)
        bad["llm_control"] = "ALLOW"
        r = validate_ficha(bad)
        self.assertFalse(r["ok"])
        self.assertTrue(any(x.startswith("LLM_NOT_DENY") for x in r["reason_codes"]))

    def test_gate_load_ok(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "ficha.v2.json"
            p.write_text(json.dumps(VALID), encoding="utf-8")
            r = gate_load(td)
            self.assertTrue(r["ok"])

    def test_gate_load_missing_file(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(EnchufeGateError) as ctx:
                gate_load(td)
            self.assertEqual(ctx.exception.reason_code, "FICHA_MISSING")

    def test_gate_load_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            bad = dict(VALID)
            bad["llm_control"] = "PERMIT"
            (Path(td) / "ficha.v2.json").write_text(json.dumps(bad), encoding="utf-8")
            with self.assertRaises(EnchufeGateError) as ctx:
                gate_load(td)
            self.assertEqual(ctx.exception.reason_code, "FICHA_REJECTED")


if __name__ == "__main__":
    unittest.main()
