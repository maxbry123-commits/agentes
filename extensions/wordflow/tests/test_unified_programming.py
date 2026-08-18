# -*- coding: utf-8 -*-
"""S7/T5 — tests unified path + attestation T1 + policy snapshot fields."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.code_path_runner import run_code_path
from extensions.wordflow.engine.programming_pipeline import default_pipeline
from extensions.wordflow.engine.programming_kwargs import full_pass_kwargs, minimal_block_kwargs
from extensions.wordflow.standards.path_resolve import resolve_path, find_repo_root, default_scan_roots
from extensions.wordflow.standards.quality_handlers import resolve_py_paths
from extensions.wordflow.standards.evidence_merge import merge_evidence
from extensions.wordflow.standards.checklist_factory import checklist_from_dict
from extensions.wordflow.standards.evidence_verifier import EvidenceVerifier, EvidenceRef

TEXT = "Objetivo: test unified programming path determinista con forensic gates Wordflow."


class TestPathResolve(unittest.TestCase):
    def test_find_repo_root(self):
        r = find_repo_root()
        self.assertTrue(r.exists() or r.name)

    def test_default_scan_roots(self):
        roots = default_scan_roots()
        self.assertGreaterEqual(len(roots), 1)

    def test_resolve_runner_path(self):
        p = resolve_path("extensions/wordflow/engine/code_path_runner.py")
        self.assertTrue(p.name.endswith(".py") or p.name == "code_path_runner.py")


class TestEvidenceMerge(unittest.TestCase):
    def test_complete_defaults(self):
        m = merge_evidence(engine_packet={"task_id": "T1", "claim_status": "PARTIAL", "paths": [{"path": "a.py"}]}, mission_id="M1", task_id="T1")
        self.assertTrue(m["complete"])


class TestChecklistFactory(unittest.TestCase):
    def test_from_dict(self):
        c = checklist_from_dict({"mission_id": "m", "task_id": "t", "action": "GENERATE", "claims": []})
        self.assertEqual(c.mission_id, "m")

    def test_auto_core_without_evidence_empty(self):
        c = checklist_from_dict({"mission_id": "m", "task_id": "t", "auto_core_claims": True})
        self.assertEqual(len(c.claims), 0)


class TestEvidenceVerifierT6(unittest.TestCase):
    def test_reject_placeholder(self):
        v = EvidenceVerifier()
        r = v.verify_ref(EvidenceRef("measure", "auto_core_placeholder"))
        self.assertFalse(r["ok"])


class TestAttestationT1(unittest.TestCase):
    def test_full_pass_requires_attestation(self):
        with self.assertRaises(RuntimeError):
            full_pass_kwargs(mission_id="x")

    def test_full_pass_with_attestation(self):
        kw = full_pass_kwargs(mission_id="x", ci_attestation=True, attestation_source="unit")
        self.assertTrue(kw.get("_ci_attestation"))


class TestUnified(unittest.TestCase):
    def test_run_unified_block_without_measures(self):
        r = default_pipeline().run_unified(TEXT, **minimal_block_kwargs())
        self.assertFalse(r["ok"])
        self.assertEqual(r["llm_control"], "DENY")

    def test_run_unified_pass_with_full_kwargs(self):
        r = default_pipeline().run_unified(
            TEXT,
            **full_pass_kwargs(mission_id="u1", ci_attestation=True, attestation_source="unit"),
        )
        self.assertTrue(r["ok"], msg=str(r.get("forensic") or r.get("stages")))

    def test_runner_statuses(self):
        r = run_code_path(
            TEXT,
            **full_pass_kwargs(mission_id="c1", ci_attestation=True, attestation_source="unit"),
        )
        self.assertEqual(r.get("c_status"), "C1-C7_CLOSED")
        self.assertEqual(r.get("s_status"), "S1-S8_CLOSED")
        self.assertIn("policy", r)
        self.assertEqual(r["llm_control"], "DENY")


if __name__ == "__main__":
    unittest.main()
