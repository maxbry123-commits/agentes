# -*- coding: utf-8 -*-
"""A-SE-05 tests — provenance."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from source_evolution.engine.provenance import build_provenance  # noqa: E402
from source_evolution.engine.version_pin import normalize_pin  # noqa: E402


def _pin():
    return normalize_pin({
        "schema_version": "1.0",
        "pin_id": "pin-prov",
        "source_type": "git",
        "locator": {"uri": "https://github.com/x/y.git"},
        "digest": {
            "algo": "git_commit",
            "value": "abcdef0123456789abcdef0123456789abcdef01",
        },
        "license": "MIT",
        "meta": {"note": "ok", "api_token": "secret123"},
    })


class TestProvenance(unittest.TestCase):
    def test_build(self):
        p = build_provenance(
            pin=_pin(),
            fetch_result={"status": "SUCCESS"},
            install_plan={"status": "PLANNED"},
        )
        self.assertEqual(p["pin_id"], "pin-prov")
        self.assertEqual(len(p["evidence_hash"]), 64)
        self.assertEqual(p["meta"]["api_token"], "***REDACTED***")
        self.assertEqual(p["meta"]["note"], "ok")
        self.assertEqual(p["llm_control"], "DENY")

    def test_no_token_in_json(self):
        p = build_provenance(pin=_pin())
        raw = str(p)
        self.assertNotIn("secret123", raw)


if __name__ == "__main__":
    unittest.main()
