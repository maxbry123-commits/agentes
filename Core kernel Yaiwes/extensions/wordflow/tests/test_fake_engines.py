# -*- coding: utf-8 -*-
"""Tests T4 FakeEngine stubs."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.engine_abi import make_job
from extensions.wordflow.engine.engines.fake_engine import (
    EchoFakeEngine,
    ErrorFakeEngine,
    PlanningFakeEngine,
    StaticFakeEngine,
)
from extensions.wordflow.engine.goal_lock import create_goal_lock
from extensions.wordflow.engine.goals_compiler import compile_goals
from extensions.wordflow.engine.input_compiler import compile_input_contract
from extensions.wordflow.engine.runtime_bus import RuntimeBus
from extensions.wordflow.engine.structured_questions import answer, build_from_contract


class TestFakeEngines(unittest.TestCase):
    def _lock_and_job(self, text_for_align: str):
        c = compile_input_contract(
            f"objective: {text_for_align}\nsuccess: ok\n"
        )
        form = answer(build_from_contract(c), "Q12_approver", "director")
        lock = create_goal_lock(compile_goals(form))
        job = make_job(
            lock_id=lock["lock_id"],
            engine_id="fake_static",
            route="ANALYSIS",
            prompt="run",
            manifest_id="man_t4",
        )
        return lock, job

    def test_static_via_bus(self):
        text = "fake static engine via bus"
        lock, job = self._lock_and_job(text)
        job["engine_id"] = "fake_static"
        bus = RuntimeBus()
        bus.register(StaticFakeEngine(output_text=text))
        res = bus.dispatch(job, lock=lock, manifest={"manifest_id": "man_t4"})
        self.assertEqual(res["status"], "OK")
        self.assertEqual(res["output_text"], text)

    def test_echo(self):
        eng = EchoFakeEngine()
        job = make_job(
            lock_id="gl",
            engine_id="fake_echo",
            route="ANALYSIS",
            prompt="hello",
            echo_block="LOCK",
            manifest_id="m",
        )
        res = eng.run(job)
        self.assertIn("hello", res["output_text"] or "")
        self.assertIn("LOCK", res["output_text"] or "")

    def test_error_engine(self):
        eng = ErrorFakeEngine()
        job = make_job(
            lock_id="gl",
            engine_id="fake_error",
            route="ANALYSIS",
            prompt="x",
            manifest_id="m",
        )
        res = eng.run(job)
        self.assertEqual(res["status"], "ERROR")

    def test_planning_fake(self):
        eng = PlanningFakeEngine()
        job = make_job(
            lock_id="gl",
            engine_id="fake_planning",
            route="PLANNING",
            prompt="plan",
            manifest_id="m",
        )
        res = eng.run(job)
        self.assertEqual(res["status"], "OK")
        self.assertTrue(res.get("artifacts"))


if __name__ == "__main__":
    unittest.main()
