# -*- coding: utf-8 -*-
"""Tests C-09 cognitive_loop — offline, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.cognitive_loop import CognitiveLoopError, run_cognitive_loop
from extensions.wordflow.engine.evidence_packet import verify_evidence_packet


class TestCognitiveLoop(unittest.TestCase):
    def test_run(self):
        r = run_cognitive_loop(
            topic="ship feature",
            plan_steps=["analyze", "compile", "deploy"],
            mission_id="m-c09",
            task_class="CODE",
            risks=["license"],
        )
        self.assertTrue(r["ok"])
        self.assertEqual(r["task_graph"]["node_count"], 3)
        self.assertTrue(verify_evidence_packet(r["evidence"])["ok"])
        self.assertEqual(r["llm_control"], "DENY")

    def test_empty_plan(self):
        with self.assertRaises(CognitiveLoopError):
            run_cognitive_loop(topic="x", plan_steps=[])


if __name__ == "__main__":
    unittest.main()
