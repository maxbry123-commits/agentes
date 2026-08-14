# -*- coding: utf-8 -*-
"""Tests T5 ExecutionManifest + bus gate."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.engine_abi import make_job
from extensions.wordflow.engine.engines.fake_engine import StaticFakeEngine
from extensions.wordflow.engine.execution_manifest import (
    attach_manifest_to_job,
    job_matches_manifest,
    sign_manifest,
    verify_manifest,
)
from extensions.wordflow.engine.goal_lock import create_goal_lock
from extensions.wordflow.engine.goals_compiler import compile_goals
from extensions.wordflow.engine.input_compiler import compile_input_contract
from extensions.wordflow.engine.runtime_bus import RuntimeBus
from extensions.wordflow.engine.structured_questions import answer, build_from_contract


class TestExecutionManifest(unittest.TestCase):
    def _lock(self):
        c = compile_input_contract(
            "objective: execution manifest sign\n"
            "success: verify hash ok\n"
            "forbidden: tamper prompt\n"
        )
        form = answer(build_from_contract(c), "Q12_approver", "director")
        return create_goal_lock(compile_goals(form))

    def test_sign_verify(self):
        lock = self._lock()
        job = make_job(
            lock_id=lock["lock_id"],
            engine_id="fake_static",
            route="ANALYSIS",
            prompt="hello",
        )
        man = sign_manifest(lock=lock, job=job)
        self.assertTrue(verify_manifest(man)["ok"])

    def test_tamper_detected(self):
        lock = self._lock()
        job = make_job(
            lock_id=lock["lock_id"],
            engine_id="fake_static",
            route="ANALYSIS",
            prompt="hello",
        )
        man = sign_manifest(lock=lock, job=job)
        man["engine_id"] = "hacked"
        self.assertFalse(verify_manifest(man)["ok"])

    def test_bus_requires_valid_manifest(self):
        lock = self._lock()
        text = "execution manifest sign verify hash ok"
        job0 = make_job(
            lock_id=lock["lock_id"],
            engine_id="fake_static",
            route="ANALYSIS",
            prompt=text,
        )
        man = sign_manifest(lock=lock, job=job0)
        job = attach_manifest_to_job(job0, man)
        bus = RuntimeBus()
        bus.register(StaticFakeEngine(output_text=text))
        res = bus.dispatch(job, lock=lock, manifest=man)
        self.assertEqual(res["status"], "OK")

        # prompt change after sign → DENY
        job_bad = dict(job)
        job_bad["input"] = dict(job["input"])
        job_bad["input"]["prompt"] = "tampered"
        res2 = bus.dispatch(job_bad, lock=lock, manifest=man)
        self.assertEqual(res2["status"], "DENIED")


if __name__ == "__main__":
    unittest.main()
