# -*- coding: utf-8 -*-
"""Tests T36 WorkflowDNA."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.loop_bridge import bridge_to_lock
from extensions.wordflow.engine.workflow_dna import compile_dna, verify_dna


class TestWorkflowDNA(unittest.TestCase):
    def test_compile_verify(self):
        lock = bridge_to_lock(
            "objective: dna t36\nsuccess: hash\nconstraint: 0% LLM\n"
        )["lock"]
        dna = compile_dna(lock, policies={"llm": "DENY"})
        self.assertTrue(verify_dna(dna)["ok"])
        self.assertEqual(dna["lock_id"], lock["lock_id"])

    def test_tamper(self):
        lock = bridge_to_lock("objective: tamper\nsuccess: fail\n")["lock"]
        dna = compile_dna(lock)
        dna["objectives"] = ["mutated"]
        self.assertFalse(verify_dna(dna)["ok"])


if __name__ == "__main__":
    unittest.main()
