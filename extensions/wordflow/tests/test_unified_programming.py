# -*- coding: utf-8 -*-
"""S7 — tests unified path + main_12 programming_path. Offline 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.code_path_runner import run_code_path
from extensions.wordflow.engine.programming_pipeline import default_pipeline
from extensions.wordflow.engine.programming_kwargs import full_pass_kwargs, minimal_block_kwargs
from extensions.wordflow.standards.path_resolve import resolve_path
from extensions.wordflow.standards.quality_handlers import resolve_py_paths
from extensions.wordflow.standards.evidence_merge import merge_evidence
from extensions.wordflow.standards.checklist_factory import checklist_from_dict

TEXT = "Objetivo: test unified programming path determinista con forensic gates Wordflow."


class TestPathResolve(unittest.TestCase):
    def test_resolve_runner_path(self):
        p = resolve_path("extensions/wordflow/engine/code_path_runner.py")
        self.assertTrue(str(p).endswith("code_path_runner.py") or p.name == "code_path_runner.py")

    def test_resolve_py_paths_handlers(self):
        found = resolve_py_paths(["extensions/wordflow/engine/code_path_runner.py"])
        # may be empty if package not installed on disk layout; still must not crash
        self.assertIsInstance(found, list)


class TestEvidenceMerge(unittest.TestCase):
    def test_complete_defaults(self):
        m = merge_evidence(engine_packet={"task_id": "T1", "claim_status": "PARTIAL", "paths": [{"path": "a.py"}]}, mission_id="M1", task_id="T1")
        self.assertTrue(m["complete"])
        self.assertEqual(m["merged"]["mission_id"], "M1")


class TestChecklistFactory(unittest.TestCase):
    def test_from_dict(self):
        c = checklist_from_dict({"mission_id": "m", "task_id": "t", "action": "GENERATE", "claims": []})
        self.assertEqual(c.mission_id, "m")
        self.assertEqual(c.action, "GENERATE")


class TestUnified(unittest.TestCase):
    def test_run_unified_block_without_measures(self):
        r = default_pipeline().run_unified(TEXT, **minimal_block_kwargs())
        self.assertFalse(r["ok"])
        self.assertEqual(r["llm_control"], "DENY")

    def test_run_unified_pass_with_full_kwargs(self):
        r = default_pipeline().run_unified(TEXT, **full_pass_kwargs(mission_id="u1"))
        self.assertTrue(r["ok"], msg=str(r.get("forensic") or r.get("stages")))
        self.assertEqual(r["path"], "UNIFIED_PIPELINE_V1")

    def test_runner_c_status(self):
        r = run_code_path(TEXT, **full_pass_kwargs(mission_id="c1"))
        self.assertEqual(r.get("c_status"), "C1-C7_CLOSED")
        self.assertEqual(r["llm_control"], "DENY")


if __name__ == "__main__":
    unittest.main()
