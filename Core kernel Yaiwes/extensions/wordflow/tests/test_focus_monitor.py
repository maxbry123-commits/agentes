# -*- coding: utf-8 -*-
"""Tests T0g FocusMonitor."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.focus_monitor import evaluate_focus, focus_gate
from extensions.wordflow.engine.goal_lock import create_goal_lock
from extensions.wordflow.engine.goals_compiler import compile_goals
from extensions.wordflow.engine.input_compiler import compile_input_contract
from extensions.wordflow.engine.structured_questions import answer, build_from_contract


class TestFocusMonitor(unittest.TestCase):
    def _lock(self):
        c = compile_input_contract(
            "objective: monitorear foco del agente\n"
            "success: band HIGH o MED cuando alineado\n"
            "forbidden: abandonar tarea\n"
        )
        form = build_from_contract(c)
        form = answer(form, "Q12_approver", "director")
        return create_goal_lock(compile_goals(form))

    def test_high_when_aligned(self):
        lock = self._lock()
        r = evaluate_focus(
            lock,
            current_step="monitorear foco",
            last_output="monitorear foco del agente en curso",
        )
        self.assertIn(r["band"], ("HIGH", "MED"))
        self.assertFalse(r["below_threshold"])
        self.assertTrue(r["signals"]["lock_ok"])

    def test_low_when_drift(self):
        lock = self._lock()
        r = evaluate_focus(
            lock,
            current_step="cocina",
            last_output="receta de pizza",
            threshold=0.5,
        )
        self.assertTrue(r["below_threshold"])
        self.assertIn(r["band"], ("LOW", "ZERO", "MED"))

    def test_gate_pass_fail(self):
        lock = self._lock()
        ok = focus_gate(
            lock,
            current_step="monitorear foco del agente",
            last_output="monitorear foco",
        )
        self.assertTrue(ok["ok"])
        bad = focus_gate(
            lock,
            current_step="otro",
            last_output="abandonar tarea ahora",
        )
        self.assertFalse(bad["ok"])


if __name__ == "__main__":
    unittest.main()
