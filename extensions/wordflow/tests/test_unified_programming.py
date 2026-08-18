# -*- coding: utf-8 -*-
"""Tests unified + T1 attestation + T6 + T7 policy."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.code_path_runner import run_code_path
from extensions.wordflow.engine.programming_pipeline import default_pipeline
from extensions.wordflow.engine.programming_kwargs import full_pass_kwargs, minimal_block_kwargs
from extensions.wordflow.standards.path_resolve import resolve_path, find_repo_root, default_scan_roots
from extensions.wordflow.standards.evidence_merge import merge_evidence
from extensions.wordflow.standards.checklist_factory import checklist_from_dict
from extensions.wordflow.standards.evidence_verifier import EvidenceVerifier, EvidenceRef

TEXT = "Objetivo: test unified programming path determinista con forensic gates Wordflow."


class TestPathResolve(unittest.TestCase):
    def test_find_repo_root(self):
        r = find_repo_root()
        self.assertTrue(r is not None)

    def test_default_scan_roots(self):
        self.assertGreaterEqual(len(default_scan_roots()), 1)


class TestEvidence(unittest.TestCase):
    def test_merge_complete(self):
        m = merge_evidence(engine_packet={"task_id": "T1", "claim_status": "PARTIAL"}, mission_id="M1", task_id="T1")
        self.assertTrue(m["complete"])

    def test_reject_placeholder(self):
        self.assertFalse(EvidenceVerifier().verify_ref(EvidenceRef("measure", "auto_core_placeholder"))["ok"])


class TestChecklist(unittest.TestCase):
    def test_auto_core_empty_without_evidence(self):
        c = checklist_from_dict({"mission_id": "m", "task_id": "t", "auto_core_claims": True})
        self.assertEqual(len(c.claims), 0)


class TestAttestation(unittest.TestCase):
    def test_requires_flag(self):
        with self.assertRaises(RuntimeError):
            full_pass_kwargs(mission_id="x")

    def test_with_flag(self):
        kw = full_pass_kwargs(mission_id="x", ci_attestation=True, attestation_source="unit")
        self.assertTrue(kw["_ci_attestation"])


class TestUnified(unittest.TestCase):
    def test_block_minimal(self):
        r = default_pipeline().run_unified(TEXT, **minimal_block_kwargs())
        self.assertFalse(r["ok"])
        self.assertIn("policy", r)

    def test_pass_attested(self):
        r = default_pipeline().run_unified(
            TEXT,
            **{k: v for k, v in full_pass_kwargs(mission_id="u1", ci_attestation=True, attestation_source="unit").items() if not k.startswith("_")},
        )
        self.assertTrue(r["ok"], msg=str(r.get("forensic")))
        self.assertIn("policy", r)
        self.assertEqual(r.get("t_status"), "T1-T8_CLOSED")

    def test_runner_statuses(self):
        kw = {k: v for k, v in full_pass_kwargs(mission_id="c1", ci_attestation=True, attestation_source="unit").items() if not k.startswith("_")}
        r = run_code_path(TEXT, **kw)
        self.assertEqual(r.get("c_status"), "C1-C7_CLOSED")
        self.assertEqual(r.get("s_status"), "S1-S8_CLOSED")
        self.assertEqual(r["llm_control"], "DENY")


if __name__ == "__main__":
    unittest.main()
