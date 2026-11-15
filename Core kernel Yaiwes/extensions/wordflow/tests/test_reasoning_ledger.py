# -*- coding: utf-8 -*-
"""Tests T0l ReasoningLedger."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from extensions.wordflow.engine.goal_lock import create_goal_lock
from extensions.wordflow.engine.goals_compiler import compile_goals
from extensions.wordflow.engine.input_compiler import compile_input_contract
from extensions.wordflow.engine.reasoning_ledger import GENESIS_PREV, ReasoningLedger
from extensions.wordflow.engine.structured_questions import answer, build_from_contract


class TestReasoningLedger(unittest.TestCase):
    def _lock(self):
        c = compile_input_contract(
            "objective: registrar decision memory\n"
            "success: frame chain verifica OK\n"
            "forbidden: reescribir frames\n"
        )
        form = build_from_contract(c)
        form = answer(form, "Q12_approver", "director")
        return create_goal_lock(compile_goals(form))

    def test_append_chain(self):
        lock = self._lock()
        led = ReasoningLedger()
        f1 = led.append_frame(
            lock,
            decision="aceptar plan A",
            evidence=["test_pass"],
            alternatives=["plan B"],
            refutations=["B mas caro"],
            confidence=0.8,
        )
        f2 = led.append_frame(
            lock,
            decision="ejecutar paso 1",
            tools=["compiler"],
            artifacts=["a.py"],
            checkpoint_id="cp1",
        )
        self.assertEqual(f1["seq"], 1)
        self.assertEqual(f1["prev_hash"], GENESIS_PREV)
        self.assertEqual(f2["prev_hash"], f1["frame_hash"])
        self.assertEqual(f1["goal"], lock["objective"])
        self.assertTrue(led.verify_chain()["ok"])

    def test_no_rewrite(self):
        led = ReasoningLedger()
        led.append_frame(self._lock(), decision="x")
        with self.assertRaises(RuntimeError):
            led.rewrite_forbidden()

    def test_persist(self):
        lock = self._lock()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ledger.jsonl"
            a = ReasoningLedger(path)
            a.append_frame(lock, decision="d1")
            b = ReasoningLedger(path)
            self.assertEqual(b.length, 1)
            self.assertTrue(b.verify_chain()["ok"])

    def test_corrupt_lock_rejected(self):
        lock = self._lock()
        lock["objective"] = "tampered"
        led = ReasoningLedger()
        with self.assertRaises(ValueError):
            led.append_frame(lock, decision="x")


if __name__ == "__main__":
    unittest.main()
