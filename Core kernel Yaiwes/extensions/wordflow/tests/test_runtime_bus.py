# -*- coding: utf-8 -*-
"""Tests T2 RuntimeBus."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.engine_abi import make_job, make_result
from extensions.wordflow.engine.goal_lock import create_goal_lock
from extensions.wordflow.engine.goals_compiler import compile_goals
from extensions.wordflow.engine.input_compiler import compile_input_contract
from extensions.wordflow.engine.runtime_bus import RuntimeBus
from extensions.wordflow.engine.structured_questions import answer, build_from_contract


class FakeEngine:
    engine_id = "fake"

    def __init__(self, text: str = "ok"):
        self.text = text

    def run(self, job):
        return make_result(job, status="OK", output_text=self.text)


class TestRuntimeBus(unittest.TestCase):
    def _lock(self):
        c = compile_input_contract(
            "objective: runtime bus dispatch\n"
            "success: deny sin manifest\n"
            "forbidden: saltar bus\n"
        )
        form = answer(build_from_contract(c), "Q12_approver", "director")
        return create_goal_lock(compile_goals(form))

    def test_deny_without_manifest(self):
        lock = self._lock()
        bus = RuntimeBus()
        bus.register(FakeEngine("runtime bus dispatch deny sin manifest"))
        job = make_job(
            lock_id=lock["lock_id"],
            engine_id="fake",
            route="ANALYSIS",
            prompt="x",
            manifest_id=None,
        )
        res = bus.dispatch(job, lock=lock)
        self.assertEqual(res["status"], "DENIED")
        self.assertEqual(res["error_code"], "MANIFEST_REQUIRED")

    def test_dispatch_ok(self):
        lock = self._lock()
        text = "runtime bus dispatch con deny sin manifest sin saltar bus"
        bus = RuntimeBus()
        bus.register(FakeEngine(text))
        job = make_job(
            lock_id=lock["lock_id"],
            engine_id="fake",
            route="ANALYSIS",
            prompt="x",
            manifest_id="man_1",
        )
        res = bus.dispatch(job, lock=lock, manifest={"manifest_id": "man_1"})
        self.assertEqual(res["status"], "OK")

    def test_engine_not_registered(self):
        lock = self._lock()
        bus = RuntimeBus()
        job = make_job(
            lock_id=lock["lock_id"],
            engine_id="missing",
            route="ANALYSIS",
            prompt="x",
            manifest_id="man_1",
        )
        res = bus.dispatch(job, lock=lock, manifest={"manifest_id": "man_1"})
        self.assertEqual(res["error_code"], "ENGINE_NOT_REGISTERED")


if __name__ == "__main__":
    unittest.main()
