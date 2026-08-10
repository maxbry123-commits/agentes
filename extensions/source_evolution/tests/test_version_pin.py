# -*- coding: utf-8 -*-
"""A-SE-01 tests — VersionPin + registry."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from source_evolution.engine.registry import SourceRegistry  # noqa: E402
from source_evolution.engine.version_pin import (  # noqa: E402
    VersionPinError,
    normalize_pin,
    pins_equal,
)


def _pin(**kw):
    b = {
        "schema_version": "1.0",
        "pin_id": "pin-qwen-01",
        "source_type": "git",
        "locator": {
            "uri": "https://github.com/QwenLM/Qwen2.5.git",
            "ref": "main",
        },
        "digest": {
            "algo": "git_commit",
            "value": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
        },
        "license": "Apache-2.0",
        "llm_control": "DENY",
    }
    b.update(kw)
    return b


class TestVersionPin(unittest.TestCase):
    def test_normalize(self):
        p = normalize_pin(_pin())
        self.assertEqual(p["source_type"], "git")
        self.assertEqual(len(p["pin_hash"]), 64)
        self.assertEqual(p["llm_control"], "DENY")

    def test_bad_source_type(self):
        with self.assertRaises(VersionPinError) as ctx:
            normalize_pin(_pin(source_type="ftp"))
        self.assertEqual(ctx.exception.reason_code, "INVALID_SOURCE_TYPE")

    def test_bad_sha256(self):
        with self.assertRaises(VersionPinError) as ctx:
            normalize_pin(_pin(digest={"algo": "sha256", "value": "deadbeef"}))
        self.assertEqual(ctx.exception.reason_code, "INVALID_DIGEST_VALUE")

    def test_missing_uri(self):
        with self.assertRaises(VersionPinError) as ctx:
            normalize_pin(_pin(locator={"ref": "main"}))
        self.assertEqual(ctx.exception.reason_code, "INVALID_LOCATOR")

    def test_pins_equal(self):
        a = normalize_pin(_pin())
        b = normalize_pin(_pin(pin_id="other"))
        self.assertTrue(pins_equal(a, b))

    def test_registry_register_get(self):
        reg = SourceRegistry()
        p = reg.register(_pin())
        self.assertEqual(reg.get("pin-qwen-01")["pin_id"], "pin-qwen-01")
        self.assertEqual(len(reg.list_pins()), 1)
        self.assertEqual(p["digest"]["algo"], "git_commit")

    def test_registry_conflict(self):
        reg = SourceRegistry()
        reg.register(_pin())
        with self.assertRaises(VersionPinError) as ctx:
            reg.register(
                _pin(
                    digest={
                        "algo": "git_commit",
                        "value": "ffffffffffffffffffffffffffffffffffffffff",
                    }
                )
            )
        self.assertEqual(ctx.exception.reason_code, "PIN_ID_CONFLICT")

    def test_registry_persist(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "pins.json"
            reg = SourceRegistry(path)
            reg.register(_pin())
            reg2 = SourceRegistry(path)
            self.assertIsNotNone(reg2.get("pin-qwen-01"))

    def test_find_by_digest(self):
        reg = SourceRegistry()
        reg.register(_pin())
        found = reg.find_by_digest(
            "git_commit", "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0"
        )
        self.assertEqual(len(found), 1)


if __name__ == "__main__":
    unittest.main()
