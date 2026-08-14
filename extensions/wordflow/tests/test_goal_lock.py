# -*- coding: utf-8 -*-
"""Tests T0e GoalLock."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.goal_lock import (
    GoalLockError,
    create_goal_lock,
    release_lock,
    validate_against_lock,
    verify_lock_integrity,
)
from extensions.wordflow.engine.goals_compiler import compile_goals
from extensions.wordflow.engine.input_compiler import compile_input_contract
from extensions.wordflow.engine.structured_questions import answer, build_from_contract


class TestGoalLock(unittest.TestCase):
    def _compiled(self):
        c = compile_input_contract(
            "objective: implementar goal lock inmutable\n"
            "success: tests PASS y hash estable\n"
            "constraint: 0% LLM\n"
            "forbidden: reescribir objective\n"
        )
        form = build_from_contract(c)
        form = answer(form, "Q12_approver", "director")
        return compile_goals(form)

    def test_create_locked(self):
        goals = self._compiled()
        lock = create_goal_lock(goals)
        self.assertEqual(lock["status"], "LOCKED")
        self.assertIn("goal lock", lock["objective"].lower())
        self.assertEqual(len(lock["lock_hash"]), 64)
        self.assertTrue(verify_lock_integrity(lock)["ok"])

    def test_reject_not_compiled(self):
        with self.assertRaises(GoalLockError):
            create_goal_lock({"status": "BLOCKED_UNRESOLVED_FORM", "goals": {}})

    def test_tamper_detected(self):
        lock = create_goal_lock(self._compiled())
        lock["objective"] = "hacked"
        self.assertFalse(verify_lock_integrity(lock)["ok"])

    def test_validate_forbidden(self):
        lock = create_goal_lock(self._compiled())
        r = validate_against_lock(lock, "voy a reescribir objective ahora")
        self.assertFalse(r["ok"])
        self.assertEqual(r["action"], "DISCARD_OUTPUT")

    def test_validate_aligned(self):
        lock = create_goal_lock(self._compiled())
        r = validate_against_lock(
            lock,
            "implementar goal lock inmutable con tests PASS y hash estable sin reescribir",
        )
        self.assertTrue(r["ok"])

    def test_release(self):
        lock = create_goal_lock(self._compiled())
        rel = release_lock(lock)
        self.assertEqual(rel["status"], "RELEASED")
        self.assertEqual(lock["status"], "LOCKED")  # original intact


if __name__ == "__main__":
    unittest.main()
