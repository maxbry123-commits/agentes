# -*- coding: utf-8 -*-
"""Tests T0a InputCompiler — literal, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.input_compiler import (
    compile_input_contract,
    compile_or_reason,
)
from extensions.wordflow.engine.input_normalizer import InputBlockError


class TestInputCompiler(unittest.TestCase):
    def test_complete_from_string(self):
        text = (
            "objective: crear schema input_contract\n"
            "success: tests PASS y archivo en github\n"
            "constraint: 0% LLM\n"
            "forbidden: inventar campos\n"
            "rollback: revert commit\n"
        )
        c = compile_input_contract(text)
        self.assertEqual(c["status"], "COMPLETE")
        self.assertEqual(c["missing_fields"], [])
        self.assertIn("crear schema", c["objective"])
        self.assertIn("tests PASS", c["success_criteria"])
        self.assertEqual(c["constraints"], ["0% LLM"])
        self.assertEqual(c["forbidden"], ["inventar campos"])
        self.assertTrue(c["literal_mode"])
        self.assertEqual(c["raw_literal"], text.strip())
        self.assertEqual(len(c["contract_hash"]), 64)

    def test_incomplete_missing_objective(self):
        text = "success: algo funciona\n"
        c = compile_input_contract(text)
        self.assertEqual(c["status"], "INCOMPLETE")
        self.assertIn("objective", c["missing_fields"])

    def test_from_input_block_dict(self):
        raw = {
            "schema_version": "1.0",
            "block_id": "blk_test_01",
            "source_type": "document",
            "raw_text": "objective: auditar pipeline\nsuccess: claim CONFIRMADO\n",
            "quality_bar": "never_MVP",
            "goals_hint": [],
            "priority": "P0",
        }
        c = compile_input_contract(raw)
        self.assertEqual(c["source"]["block_id"], "blk_test_01")
        self.assertEqual(c["source"]["source_type"], "document")
        self.assertEqual(c["priority"], "P0")
        self.assertEqual(c["status"], "COMPLETE")

    def test_goals_hint_fallback_objective(self):
        raw = {
            "schema_version": "1.0",
            "block_id": "blk_hint",
            "source_type": "chat",
            "raw_text": "success: ok\n",
            "quality_bar": "standard",
            "goals_hint": ["implementar GoalLock"],
        }
        c = compile_input_contract(raw)
        self.assertEqual(c["objective"], "implementar GoalLock")
        self.assertEqual(c["status"], "COMPLETE")

    def test_secret_rejected(self):
        raw = {
            "schema_version": "1.0",
            "block_id": "blk_sec",
            "source_type": "chat",
            "raw_text": "objective: x\nsuccess: y\napi_key: ghp_secretvalue\n",
            "quality_bar": "standard",
            "goals_hint": [],
        }
        with self.assertRaises(InputBlockError):
            compile_input_contract(raw)

    def test_compile_or_reason_ok(self):
        ok, c = compile_or_reason(
            "objective: test\nsuccess: pass\n"
        )
        self.assertTrue(ok)
        self.assertEqual(c["status"], "COMPLETE")

    def test_risk_guess_high(self):
        c = compile_input_contract(
            "objective: delete production data\nsuccess: done\n"
        )
        self.assertEqual(c["risk_level"], "high")


if __name__ == "__main__":
    unittest.main()
