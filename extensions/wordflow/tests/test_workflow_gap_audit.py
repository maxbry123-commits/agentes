# -*- coding: utf-8 -*-
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from extensions.wordflow.engine.programming_pipeline import default_pipeline
from extensions.wordflow.standards.workflow_gap_audit import audit_programming_workflow

TEXT = "Objetivo: auditar gap workflow wordflow determinista con contexto verificado."


class TestWorkflowGapAudit(unittest.TestCase):
    def test_current_repo_has_no_blocking_workflow_gaps(self):
        result = audit_programming_workflow(Path(__file__).resolve().parents[3])
        self.assertEqual(result["verdict"], "NO_PASS_CLAIM")
        self.assertEqual(result["blocking_gap_count"], 0, msg=str(result["gaps"]))

    def test_missing_authority_doc_prepares_solution(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            result = audit_programming_workflow(root)
        self.assertFalse(result["ok"])
        self.assertTrue(result["solutions_prepared"])
        self.assertIn("WF-AUD-001", {g["gap_id"] for g in result["gaps"]})

    def test_unified_accepts_consult_gateway_kw(self):
        result = default_pipeline().run_unified(
            TEXT,
            context_verified=True,
            handoff_verified=True,
            consult_gateway=False,
        )
        self.assertNotEqual(result.get("stage"), "kwargs")


if __name__ == "__main__":
    unittest.main()
