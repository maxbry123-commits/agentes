# -*- coding: utf-8 -*-
"""Tests T0f Push/Ping."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.goal_lock import create_goal_lock
from extensions.wordflow.engine.goals_compiler import compile_goals
from extensions.wordflow.engine.input_compiler import compile_input_contract
from extensions.wordflow.engine.push_ping import (
    PushPingSupervisor,
    compute_focus_score,
    emit_ping,
)
from extensions.wordflow.engine.structured_questions import answer, build_from_contract


class TestPushPing(unittest.TestCase):
    def _lock(self):
        c = compile_input_contract(
            "objective: mantener foco con push ping\n"
            "success: action CONTINUE cuando alineado\n"
            "forbidden: abandonar objetivo\n"
        )
        form = build_from_contract(c)
        form = answer(form, "Q12_approver", "director")
        return create_goal_lock(compile_goals(form))

    def test_continue_aligned(self):
        lock = self._lock()
        ev = emit_ping(
            lock,
            trigger="interval",
            current_step="push ping",
            last_output="mantener foco con push ping en curso",
        )
        self.assertEqual(ev["action"], "CONTINUE")
        self.assertTrue(ev["lock_integrity_ok"])
        self.assertGreaterEqual(ev["focus_score"], 0.5)

    def test_stop_on_low_focus(self):
        lock = self._lock()
        ev = emit_ping(
            lock,
            trigger="post_tool",
            current_step="otro tema",
            last_output="cocinar pasta y ver television",
            focus_threshold=0.5,
        )
        self.assertEqual(ev["action"], "STOP_REPLAN")

    def test_abort_corrupt_lock(self):
        lock = self._lock()
        lock["objective"] = "tampered"
        ev = emit_ping(lock, trigger="manual")
        self.assertEqual(ev["action"], "ABORT_CORRUPT_LOCK")

    def test_supervisor_interval_gate(self):
        lock = self._lock()
        sup = PushPingSupervisor(lock, interval_s=15)
        e1 = sup.maybe_interval_ping(now_mono=100.0, current_step="push ping")
        self.assertIsNotNone(e1)
        e2 = sup.maybe_interval_ping(now_mono=110.0, current_step="push ping")
        self.assertIsNone(e2)  # within 15s
        e3 = sup.maybe_interval_ping(now_mono=116.0, current_step="push ping")
        self.assertIsNotNone(e3)

    def test_post_tool_always(self):
        lock = self._lock()
        sup = PushPingSupervisor(lock, interval_s=15)
        ev = sup.post_tool_ping(
            current_step="push ping",
            last_output="mantener foco con push ping",
        )
        self.assertEqual(ev["trigger"], "post_tool")

    def test_focus_score_range(self):
        lock = self._lock()
        s = compute_focus_score(lock, current_step="mantener foco", last_output="push ping")
        self.assertGreaterEqual(s, 0.0)
        self.assertLessEqual(s, 1.0)


if __name__ == "__main__":
    unittest.main()
