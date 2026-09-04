# -*- coding: utf-8 -*-
"""Tests T1 Engine ABI."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.engine_abi import apply_goal_filter, make_job, make_result
from extensions.wordflow.engine.goal_lock import create_goal_lock
from extensions.wordflow.engine.goals_compiler import compile_goals
from extensions.wordflow.engine.input_compiler import compile_input_contract
from extensions.wordflow.engine.structured_questions import answer, build_from_contract


class TestEngineABI(unittest.TestCase):
    def _lock(self):
        c = compile_input_contract(
            "objective: engine abi job result\n"
            "success: hash estable\n"
            "forbidden: bypass bus\n"
        )
        form = answer(build_from_contract(c), "Q12_approver", "director")
        return create_goal_lock(compile_goals(form))

    def test_make_job_hash(self):
        job = make_job(
            lock_id="gl_1",
            engine_id="fake",
            route="REASONING",
            prompt="hello",
            echo_block="LOCK",
        )
        self.assertTrue(job["job_id"].startswith("job_"))
        self.assertEqual(len(job["job_hash"]), 64)

    def test_goal_filter_ok(self):
        lock = self._lock()
        job = make_job(
            lock_id=lock["lock_id"],
            engine_id="fake",
            route="ANALYSIS",
            prompt="x",
        )
        text = "engine abi job result con hash estable sin bypass"
        res = apply_goal_filter(lock, job, text)
        self.assertEqual(res["status"], "OK")

    def test_goal_filter_discard(self):
        lock = self._lock()
        job = make_job(
            lock_id=lock["lock_id"],
            engine_id="fake",
            route="ANALYSIS",
            prompt="x",
        )
        res = apply_goal_filter(lock, job, "voy a bypass bus ahora")
        self.assertEqual(res["status"], "DISCARDED")


if __name__ == "__main__":
    unittest.main()
