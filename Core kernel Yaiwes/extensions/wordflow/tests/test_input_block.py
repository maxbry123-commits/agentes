# -*- coding: utf-8 -*-
"""A-WF-01 tests — InputBlock normalizer."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wordflow.engine.input_normalizer import (  # noqa: E402
    InputBlockError,
    normalize_input_block,
    validate_or_reason,
)


def _base(**kw):
    b = {
        "schema_version": "1.0",
        "block_id": "IB-001",
        "source_type": "chat",
        "raw_text": "Implementar fingerprint 7 dims 0% LLM",
        "quality_bar": "never_MVP",
        "goals_hint": ["G1_fingerprint", "G2_tests"],
        "priority": "P0",
    }
    b.update(kw)
    return b


class TestInputBlock(unittest.TestCase):
    def test_valid(self):
        out = normalize_input_block(_base())
        self.assertEqual(out["schema_version"], "1.0")
        self.assertEqual(out["quality_bar"], "never_MVP")
        self.assertTrue(out["flags"]["never_mvp"])
        self.assertEqual(len(out["block_hash"]), 64)

    def test_missing_block(self):
        ok, err = validate_or_reason(None)
        self.assertFalse(ok)
        self.assertEqual(err["reason_code"], "MISSING_BLOCK")

    def test_empty_raw_text(self):
        with self.assertRaises(InputBlockError) as ctx:
            normalize_input_block(_base(raw_text="   "))
        self.assertEqual(ctx.exception.reason_code, "EMPTY_RAW_TEXT")

    def test_bad_quality_bar(self):
        with self.assertRaises(InputBlockError) as ctx:
            normalize_input_block(_base(quality_bar="mvp"))
        self.assertEqual(ctx.exception.reason_code, "INVALID_QUALITY_BAR")

    def test_bad_source_type(self):
        with self.assertRaises(InputBlockError) as ctx:
            normalize_input_block(_base(source_type="email"))
        self.assertEqual(ctx.exception.reason_code, "INVALID_SOURCE_TYPE")

    def test_secret_rejected(self):
        with self.assertRaises(InputBlockError) as ctx:
            normalize_input_block(_base(meta={"api_key": "sk-xxx"}))
        self.assertEqual(ctx.exception.reason_code, "SECRET_IN_INPUT")

    def test_missing_goals_hint(self):
        p = _base()
        del p["goals_hint"]
        with self.assertRaises(InputBlockError) as ctx:
            normalize_input_block(p)
        self.assertEqual(ctx.exception.reason_code, "MISSING_FIELD")

    def test_repair_flag(self):
        out = normalize_input_block(
            _base(source_type="repair", parent_block_id="IB-000")
        )
        self.assertTrue(out["flags"]["is_repair"])
        self.assertTrue(out["flags"]["has_parent"])

    def test_default_priority(self):
        p = _base()
        del p["priority"]
        out = normalize_input_block(p)
        self.assertEqual(out["priority"], "P1")

    def test_hash_stable(self):
        a = normalize_input_block(_base())
        b = normalize_input_block(_base())
        self.assertEqual(a["block_hash"], b["block_hash"])


if __name__ == "__main__":
    unittest.main()
