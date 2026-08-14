# -*- coding: utf-8 -*-
"""Tests T0j Cognitive Registers."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.cognitive_registers import (
    as_prompt_block,
    load_from_lock,
    merge_memory_pack,
    set_register,
)
from extensions.wordflow.engine.goal_lock import create_goal_lock
from extensions.wordflow.engine.goals_compiler import compile_goals
from extensions.wordflow.engine.input_compiler import compile_input_contract
from extensions.wordflow.engine.structured_questions import answer, build_from_contract


class TestCognitiveRegisters(unittest.TestCase):
    def _lock(self):
        c = compile_input_contract(
            "objective: cargar registros cognitivos\n"
            "success: R0 igual al objective del lock\n"
            "constraint: 0% LLM\n"
        )
        form = build_from_contract(c)
        form = answer(form, "Q12_approver", "director")
        return create_goal_lock(compile_goals(form))

    def test_load_seeds_r0(self):
        lock = self._lock()
        f = load_from_lock(lock)
        self.assertEqual(f["registers"]["R0_objective"], lock["objective"])
        self.assertEqual(len(f["registers"]), 16)
        self.assertEqual(len(f["file_hash"]), 64)

    def test_set_and_prompt(self):
        f = load_from_lock(self._lock())
        f = set_register(f, "R1_step", "implementar T0j")
        f = set_register(f, "R14_confidence", 0.9)
        block = as_prompt_block(f)
        self.assertIn("R0_objective", block)
        self.assertIn("R1_step", block)
        self.assertIn("implementar T0j", block)

    def test_merge_memory_pack(self):
        f = load_from_lock(self._lock())
        r0 = f["registers"]["R0_objective"]
        f2 = merge_memory_pack(
            f,
            {
                "facts": ["fact-a"],
                "open_loops": ["next-1"],
                "checkpoint_ref": "cp_1",
                "state": "RUNNING",
            },
        )
        self.assertEqual(f2["registers"]["R0_objective"], r0)
        self.assertIn("fact-a", f2["registers"]["R9_evidence"])
        self.assertEqual(f2["registers"]["R8_checkpoint"], "cp_1")
        self.assertEqual(f2["registers"]["R7_state"], "RUNNING")

    def test_invalid_register(self):
        f = load_from_lock(self._lock())
        with self.assertRaises(KeyError):
            set_register(f, "R99_x", "no")


if __name__ == "__main__":
    unittest.main()
