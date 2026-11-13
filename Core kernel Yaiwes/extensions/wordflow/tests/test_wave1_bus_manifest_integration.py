# -*- coding: utf-8 -*-
"""T7 — WAVE-1 integration: Job → Manifest → Bus → FakeEngine → GoalFilter → Handoff."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.cognitive_registers import load_from_lock, set_register
from extensions.wordflow.engine.engine_abi import make_job
from extensions.wordflow.engine.engines.fake_engine import ErrorFakeEngine, StaticFakeEngine
from extensions.wordflow.engine.execution_manifest import attach_manifest_to_job, sign_manifest
from extensions.wordflow.engine.goal_lock import create_goal_lock
from extensions.wordflow.engine.goals_compiler import compile_goals
from extensions.wordflow.engine.handoff import compile_handoff, validate_handoff
from extensions.wordflow.engine.input_compiler import compile_input_contract
from extensions.wordflow.engine.objective_echo import inject_echo
from extensions.wordflow.engine.runtime_bus import RuntimeBus
from extensions.wordflow.engine.structured_questions import answer, build_from_contract


class TestWave1BusManifestIntegration(unittest.TestCase):
    def _lock(self, objective: str, success: str, forbidden: str = ""):
        raw = f"objective: {objective}\nsuccess: {success}\n"
        if forbidden:
            raw += f"forbidden: {forbidden}\n"
        c = compile_input_contract(raw)
        form = answer(build_from_contract(c), "Q12_approver", "director")
        return create_goal_lock(compile_goals(form))

    def test_happy_path_to_handoff(self):
        obj = "wave1 bus manifest integration"
        lock = self._lock(obj, "result OK y handoff valido")
        echo = inject_echo(lock, "ejecutar")
        regs = set_register(load_from_lock(lock), "R1_step", "T7")

        job0 = make_job(
            lock_id=lock["lock_id"],
            engine_id="fake_static",
            route="ANALYSIS",
            prompt=f"{obj} result OK y handoff valido",
            echo_block=echo["echo"]["block"],
            registers_block=None,
        )
        man = sign_manifest(lock=lock, job=job0)
        job = attach_manifest_to_job(job0, man)

        bus = RuntimeBus()
        bus.register(StaticFakeEngine(output_text=job["input"]["prompt"]))
        res = bus.dispatch(job, lock=lock, manifest=man)
        self.assertEqual(res["status"], "OK")

        ho = compile_handoff(
            lock,
            artifacts=list(res.get("artifacts") or []),
            evidence=[f"result:{res.get('result_id')}"],
            checkpoint_id="wave1_t7",
            next_step="WAVE-2",
            registers_file=regs,
            manifest_id=man["manifest_id"],
            status="DONE",
        )
        self.assertTrue(validate_handoff(ho)["ok"])

    def test_deny_without_manifest_object(self):
        lock = self._lock("deny path", "denied")
        job = make_job(
            lock_id=lock["lock_id"],
            engine_id="fake_static",
            route="ANALYSIS",
            prompt="x",
            manifest_id="man_orphan",
        )
        bus = RuntimeBus()
        bus.register(StaticFakeEngine())
        res = bus.dispatch(job, lock=lock, manifest=None)
        self.assertEqual(res["status"], "DENIED")
        self.assertEqual(res["error_code"], "MANIFEST_OBJECT_REQUIRED")

    def test_deny_prompt_tamper(self):
        lock = self._lock("tamper test", "must deny")
        job0 = make_job(
            lock_id=lock["lock_id"],
            engine_id="fake_static",
            route="ANALYSIS",
            prompt="original",
        )
        man = sign_manifest(lock=lock, job=job0)
        job = attach_manifest_to_job(job0, man)
        job["input"] = dict(job["input"])
        job["input"]["prompt"] = "tampered"
        bus = RuntimeBus()
        bus.register(StaticFakeEngine())
        res = bus.dispatch(job, lock=lock, manifest=man)
        self.assertEqual(res["status"], "DENIED")
        self.assertEqual(res["error_code"], "PROMPT_FINGERPRINT_MISMATCH")

    def test_goal_discard_after_engine(self):
        lock = self._lock(
            "goal filter after engine",
            "discard forbidden",
            forbidden="saltar bus",
        )
        job0 = make_job(
            lock_id=lock["lock_id"],
            engine_id="fake_static",
            route="ANALYSIS",
            prompt="anything",
        )
        man = sign_manifest(lock=lock, job=job0)
        job = attach_manifest_to_job(job0, man)
        bus = RuntimeBus()
        bus.register(StaticFakeEngine(output_text="voy a saltar bus"))
        res = bus.dispatch(job, lock=lock, manifest=man)
        self.assertEqual(res["status"], "DISCARDED")

    def test_engine_error_propagates(self):
        lock = self._lock("error engine", "error status")
        job0 = make_job(
            lock_id=lock["lock_id"],
            engine_id="fake_error",
            route="ANALYSIS",
            prompt="x",
        )
        man = sign_manifest(lock=lock, job=job0)
        job = attach_manifest_to_job(job0, man)
        job["engine_id"] = "fake_error"
        # re-sign with correct engine_id
        man = sign_manifest(lock=lock, job=job)
        job = attach_manifest_to_job(job, man)
        bus = RuntimeBus()
        bus.register(ErrorFakeEngine())
        res = bus.dispatch(job, lock=lock, manifest=man)
        self.assertEqual(res["status"], "ERROR")


if __name__ == "__main__":
    unittest.main()
