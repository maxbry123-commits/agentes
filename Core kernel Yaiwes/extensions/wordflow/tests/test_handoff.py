# -*- coding: utf-8 -*-
"""Tests T6 HandoffPackage."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.cognitive_registers import load_from_lock
from extensions.wordflow.engine.goal_lock import create_goal_lock
from extensions.wordflow.engine.goals_compiler import compile_goals
from extensions.wordflow.engine.handoff import compile_handoff, validate_handoff
from extensions.wordflow.engine.input_compiler import compile_input_contract
from extensions.wordflow.engine.structured_questions import answer, build_from_contract


class TestHandoff(unittest.TestCase):
    def _lock(self):
        c = compile_input_contract(
            "objective: handoff package portable\n"
            "success: validate hash ok\n"
            "constraint: 0% LLM\n"
        )
        form = answer(build_from_contract(c), "Q12_approver", "director")
        return create_goal_lock(compile_goals(form))

    def test_compile_validate(self):
        lock = self._lock()
        regs = load_from_lock(lock)
        pkg = compile_handoff(
            lock,
            artifacts=["a.py"],
            evidence=["test_pass"],
            checkpoint_id="cp1",
            next_step="T7",
            registers_file=regs,
            status="READY",
        )
        self.assertTrue(validate_handoff(pkg)["ok"])
        self.assertEqual(pkg["goal"], lock["objective"])
        self.assertEqual(pkg["next_step"], "T7")

    def test_tamper(self):
        lock = self._lock()
        pkg = compile_handoff(lock, status="READY")
        pkg["goal"] = "hacked"
        self.assertFalse(validate_handoff(pkg)["ok"])

    def test_corrupt_lock(self):
        lock = self._lock()
        lock["objective"] = "x"
        with self.assertRaises(ValueError):
            compile_handoff(lock)


if __name__ == "__main__":
    unittest.main()
