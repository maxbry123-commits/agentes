# -*- coding: utf-8 -*-
"""Tests T0i ObjectiveEcho."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.goal_lock import GoalLockError, create_goal_lock
from extensions.wordflow.engine.goals_compiler import compile_goals
from extensions.wordflow.engine.input_compiler import compile_input_contract
from extensions.wordflow.engine.objective_echo import build_echo, inject_echo
from extensions.wordflow.engine.structured_questions import answer, build_from_contract


class TestObjectiveEcho(unittest.TestCase):
    def _lock(self):
        c = compile_input_contract(
            "objective: inyectar objective echo\n"
            "success: block contiene GOAL_LOCK\n"
            "forbidden: omitir lock\n"
        )
        form = build_from_contract(c)
        form = answer(form, "Q12_approver", "director")
        return create_goal_lock(compile_goals(form))

    def test_build_contains_objective(self):
        lock = self._lock()
        echo = build_echo(lock)
        self.assertIn("GOAL_LOCK", echo["block"])
        self.assertIn("inyectar objective echo", echo["block"])
        self.assertIn("omitir lock", echo["block"])
        self.assertEqual(len(echo["echo_hash"]), 64)

    def test_inject_prepends(self):
        lock = self._lock()
        pkg = inject_echo(lock, "escribe el codigo")
        self.assertTrue(pkg["prompt"].startswith("=== GOAL_LOCK"))
        self.assertIn("escribe el codigo", pkg["prompt"])

    def test_corrupt_lock_raises(self):
        lock = self._lock()
        lock["objective"] = "x"
        with self.assertRaises(GoalLockError):
            build_echo(lock)


if __name__ == "__main__":
    unittest.main()
