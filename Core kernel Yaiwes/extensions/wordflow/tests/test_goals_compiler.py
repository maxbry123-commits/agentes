# -*- coding: utf-8 -*-
"""Tests T0d GoalsCompiler."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.goals_compiler import compile_goals
from extensions.wordflow.engine.input_compiler import compile_input_contract
from extensions.wordflow.engine.structured_questions import answer, build_from_contract


class TestGoalsCompiler(unittest.TestCase):
    def _resolved_form(self):
        c = compile_input_contract(
            "objective: compilar goals desde form\n"
            "success: status COMPILED\n"
            "constraint: 0% LLM\n"
            "forbidden: inventar goals\n"
        )
        form = build_from_contract(c)
        form = answer(form, "Q12_approver", "director")
        return form

    def test_compile_when_resolved(self):
        form = self._resolved_form()
        out = compile_goals(form)
        self.assertEqual(out["status"], "COMPILED")
        self.assertIn("compilar goals", out["goals"]["G01_objective"])
        self.assertIn("COMPILED", out["goals"]["G05_success_criteria"])
        self.assertEqual(out["goals"]["G03_constraints"], ["0% LLM"])
        self.assertEqual(out["goals"]["G04_forbidden"], ["inventar goals"])
        self.assertEqual(out["goals"]["G12_approver"], "director")
        self.assertEqual(len(out["goals_hash"]), 64)

    def test_blocked_when_unresolved(self):
        c = compile_input_contract(
            "objective: x\nsuccess: y\n"
        )
        form = build_from_contract(c)
        # Q12 still pending
        out = compile_goals(form)
        self.assertEqual(out["status"], "BLOCKED_UNRESOLVED_FORM")
        self.assertIn("Q12_approver", out.get("pending", []))

    def test_twelve_goals_keys(self):
        form = self._resolved_form()
        out = compile_goals(form)
        self.assertEqual(len(out["goals"]), 12)


if __name__ == "__main__":
    unittest.main()
