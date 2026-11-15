# -*- coding: utf-8 -*-
"""Tests T0b StructuredQuestionsEngine."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.input_compiler import compile_input_contract
from extensions.wordflow.engine.structured_questions import (
    answer,
    build_from_contract,
    resolve_gate,
)


class TestStructuredQuestions(unittest.TestCase):
    def _complete_contract(self):
        return compile_input_contract(
            "objective: crear questions engine\n"
            "success: resolve_gate PASS\n"
            "constraint: 0% LLM\n"
        )

    def test_build_seeds_and_pending_approver(self):
        c = self._complete_contract()
        form = build_from_contract(c)
        self.assertEqual(form["schema_version"], "1.0")
        self.assertIn("Q01_objective", form["questions"])
        self.assertEqual(form["questions"]["Q01_objective"]["status"], "ANSWERED")
        self.assertEqual(form["questions"]["Q05_success_criteria"]["status"], "ANSWERED")
        # approver unknown → required still pending
        self.assertIn("Q12_approver", form["pending"])
        self.assertFalse(form["resolved"])
        gate = resolve_gate(form)
        self.assertFalse(gate["ok"])

    def test_answer_approver_resolves(self):
        c = self._complete_contract()
        form = build_from_contract(c)
        form = answer(form, "Q12_approver", "director")
        self.assertEqual(form["pending"], [])
        self.assertTrue(form["resolved"])
        gate = resolve_gate(form)
        self.assertTrue(gate["ok"])
        self.assertEqual(gate["reason"], "RESOLVED")

    def test_invalid_enum(self):
        c = self._complete_contract()
        form = build_from_contract(c)
        with self.assertRaises(ValueError):
            answer(form, "Q12_approver", "nobody")

    def test_incomplete_contract_pending_objective(self):
        c = compile_input_contract("success: only success line\n")
        form = build_from_contract(c)
        self.assertIn("Q01_objective", form["pending"])
        self.assertFalse(resolve_gate(form)["ok"])

    def test_twelve_questions_present(self):
        c = self._complete_contract()
        form = build_from_contract(c)
        self.assertEqual(len(form["questions"]), 12)


if __name__ == "__main__":
    unittest.main()
