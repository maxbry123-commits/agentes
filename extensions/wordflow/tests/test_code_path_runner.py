# -*- coding: utf-8 -*-
"""Tests C-19 code_path_runner — offline, 0% LLM, fail-closed."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.code_path_runner import run_code_path
from extensions.wordflow.standards.forensic_core import CORE_IDS, CONNECTIVITY_CHAIN, FC_IDS

TEXT = (
    "Objetivo: implementar runner del path de code determinista "
    "con quality bar y evidence packet para Wordflow."
)


def _full_measures() -> dict:
    return {cid: True for cid in CORE_IDS}


def _full_conn() -> dict:
    return {k: True for k in CONNECTIVITY_CHAIN}


def _full_fc() -> dict:
    return {fid: True for fid in FC_IDS}


class TestCodePathRunner(unittest.TestCase):
    def test_block_without_context(self):
        r = run_code_path(TEXT, mission_id="m19")
        self.assertFalse(r["ok"])
        self.assertEqual(r["stage"], "context")
        self.assertEqual(r["llm_control"], "DENY")

    def test_reject_short(self):
        r = run_code_path("x", context_verified=True, handoff_verified=True)
        self.assertFalse(r["ok"])
        self.assertEqual(r["stage"], "quality_bar")

    def test_fail_without_core_measures(self):
        r = run_code_path(
            TEXT,
            mission_id="m19",
            context_verified=True,
            handoff_verified=True,
            auto_measure_core=False,
        )
        self.assertFalse(r["ok"])
        self.assertEqual(r["llm_control"], "DENY")
        self.assertEqual(r["path"], "UNIFIED_RUNNER_V1")

    def test_pass_with_full_caller_measures(self):
        r = run_code_path(
            TEXT,
            mission_id="m19",
            context_verified=True,
            handoff_verified=True,
            core_measures=_full_measures(),
            connectivity=_full_conn(),
            counters={},
            evidence_complete=True,
            final_clean_reaudit_passed=True,
            quality_dag_ok=True,
            auto_measure_core=True,
            fc_results=_full_fc(),
        )
        self.assertTrue(r["ok"], msg=str(r.get("forensic")))
        self.assertEqual(r["verdict"], "PASS")
        self.assertEqual(r["llm_control"], "DENY")
        self.assertTrue(r["closure"]["closed"])
        self.assertEqual(r["gc_status"], "GC-01..12_WIRED")

    def test_with_skill(self):
        r = run_code_path(
            TEXT,
            skill={"package_id": "sk.path"},
            context_verified=True,
            handoff_verified=True,
            auto_measure_core=False,
        )
        self.assertIsNotNone(r.get("skill_compile"))


if __name__ == "__main__":
    unittest.main()
