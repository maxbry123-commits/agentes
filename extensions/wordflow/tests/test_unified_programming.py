# -*- coding: utf-8 -*-
"""Tests unified + U1-U10 status + U9 main_12 hook."""
from __future__ import annotations

import unittest
import inspect

from extensions.wordflow.engine.code_path_runner import run_code_path
from extensions.wordflow.engine.programming_pipeline import default_pipeline
from extensions.wordflow.engine.programming_kwargs import full_pass_kwargs, minimal_block_kwargs
from extensions.wordflow.standards.path_resolve import find_repo_root, default_scan_roots
from extensions.wordflow.standards.evidence_merge import merge_evidence
from extensions.wordflow.standards.evidence_verifier import EvidenceVerifier, EvidenceRef
from extensions.wordflow.standards.fc_auto_measure import auto_measure_fc, FC_CALLER_REQUIRED
from extensions.wordflow.standards.verdict_authority import VerdictAuthority
from extensions.wordflow.engine import main_loop

TEXT = "Objetivo: test unified programming path determinista con forensic gates Wordflow."


class TestBasics(unittest.TestCase):
    def test_roots(self):
        self.assertIsNotNone(find_repo_root())
        self.assertGreaterEqual(len(default_scan_roots()), 1)

    def test_merge(self):
        m = merge_evidence(engine_packet={"task_id": "T1", "claim_status": "PARTIAL"}, mission_id="M1", task_id="T1")
        self.assertTrue(m["complete"])

    def test_placeholder(self):
        self.assertFalse(EvidenceVerifier().verify_ref(EvidenceRef("measure", "auto_core_placeholder"))["ok"])

    def test_fc_u8(self):
        self.assertTrue(len(FC_CALLER_REQUIRED) > 0)
        r = auto_measure_fc(deterministic_path=True)
        self.assertIn("caller_required", r)

    def test_verdict_authority_u10(self):
        a = VerdictAuthority()
        self.assertIsNotNone(a.require_context(False, False))


class TestAttestation(unittest.TestCase):
    def test_requires_flag(self):
        with self.assertRaises(RuntimeError):
            full_pass_kwargs(mission_id="x")


class TestUnified(unittest.TestCase):
    def test_unknown_kwargs_u2(self):
        r = default_pipeline().run_unified(TEXT, context_verified=True, not_a_real_kw=1)
        self.assertFalse(r["ok"])
        self.assertEqual(r.get("stage"), "kwargs")

    def test_block_minimal(self):
        r = default_pipeline().run_unified(TEXT, **minimal_block_kwargs())
        self.assertFalse(r["ok"])
        self.assertIn("policy", r)
        self.assertEqual(r.get("u_status"), "U1-U10_CLOSED")

    def test_pass_attested(self):
        kw = {k: v for k, v in full_pass_kwargs(mission_id="u1", ci_attestation=True, attestation_source="unit").items() if not k.startswith("_")}
        r = default_pipeline().run_unified(TEXT, **kw)
        self.assertTrue(r["ok"], msg=str(r.get("forensic")))
        self.assertEqual(r.get("u_status"), "U1-U10_CLOSED")

    def test_runner_policy_u1(self):
        kw = {k: v for k, v in full_pass_kwargs(mission_id="c1", ci_attestation=True, attestation_source="unit").items() if not k.startswith("_")}
        r = run_code_path(TEXT, **kw)
        self.assertIn("policy", r)
        self.assertEqual(r.get("u_status"), "U1-U10_CLOSED")
        self.assertIn("stage_ms", r.get("wire_trace", {}))
        self.assertIn("quality_bar", r.get("wire_trace", {}))


class TestMain12HookU9(unittest.TestCase):
    def test_programming_path_flag_exists(self):
        sig = inspect.signature(main_loop.run_main_12)
        self.assertIn("programming_path", sig.parameters)
        self.assertIn("programming_full_pass", sig.parameters)


if __name__ == "__main__":
    unittest.main()
