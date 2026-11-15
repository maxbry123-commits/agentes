# -*- coding: utf-8 -*-
"""Tests T0p MemoryPort."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.cognitive_registers import load_from_lock
from extensions.wordflow.engine.goal_lock import create_goal_lock
from extensions.wordflow.engine.goals_compiler import compile_goals
from extensions.wordflow.engine.input_compiler import compile_input_contract
from extensions.wordflow.engine.ports.memory_port import (
    FakeHermesMemory,
    apply_memory_to_registers,
    make_memory_pack,
)
from extensions.wordflow.engine.structured_questions import answer, build_from_contract


class TestMemoryPort(unittest.TestCase):
    def _lock(self):
        c = compile_input_contract(
            "objective: memory refresh test\n"
            "success: R0 intacto tras pack\n"
            "constraint: no tocar R0\n"
        )
        form = answer(build_from_contract(c), "Q12_approver", "director")
        return create_goal_lock(compile_goals(form))

    def test_fake_refresh(self):
        lock = self._lock()
        pack = FakeHermesMemory().refresh(
            lock, current_step="t0p", last_output="ok", checkpoint_ref="cp1"
        )
        self.assertEqual(pack["engine_id"], "hermes")
        self.assertEqual(pack["lock_id"], lock["lock_id"])
        self.assertTrue(any("objective=" in f for f in pack["facts"]))

    def test_merge_preserves_r0(self):
        lock = self._lock()
        regs = load_from_lock(lock)
        r0 = regs["registers"]["R0_objective"]
        pack = FakeHermesMemory().refresh(lock, current_step="step-x")
        regs2 = apply_memory_to_registers(regs, pack)
        self.assertEqual(regs2["registers"]["R0_objective"], r0)
        self.assertTrue(regs2["registers"]["R9_evidence"])
        self.assertEqual(regs2["registers"]["R7_state"], "RUNNING")

    def test_lock_mismatch(self):
        lock = self._lock()
        regs = load_from_lock(lock)
        pack = make_memory_pack("other_lock", facts=["x"])
        with self.assertRaises(ValueError):
            apply_memory_to_registers(regs, pack)


if __name__ == "__main__":
    unittest.main()
