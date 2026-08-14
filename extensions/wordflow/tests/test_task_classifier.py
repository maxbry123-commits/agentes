# -*- coding: utf-8 -*-
"""Tests T0k TaskClassifier."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.task_classifier import classify_task, decision_gate


class TestTaskClassifier(unittest.TestCase):
    def test_deterministic(self):
        c = classify_task("correr pytest y validar schema")
        self.assertEqual(c["route"], "DETERMINISTIC")
        self.assertFalse(c["use_llm"])
        g = decision_gate(c)
        self.assertFalse(g["call_llm"])

    def test_planning_incomplete(self):
        c = classify_task("necesito planificar el sistema", form_incomplete=True)
        self.assertEqual(c["route"], "PLANNING")
        g = decision_gate(c)
        self.assertTrue(g["call_engine"])
        self.assertEqual(g["engine_hint"], "openclaw+hermes")

    def test_memory_refresh(self):
        c = classify_task("memory refresh del contexto previo")
        self.assertEqual(c["route"], "MEMORY_REFRESH")
        g = decision_gate(c)
        self.assertFalse(g["call_llm"])
        self.assertEqual(g["engine_hint"], "hermes_memory")

    def test_reasoning(self):
        c = classify_task("analiza por qué falla el diseño y propone trade-off")
        self.assertIn(c["route"], ("REASONING", "PLANNING", "ANALYSIS"))
        self.assertTrue(c["use_llm"] or c["route"] == "ANALYSIS")

    def test_explicit_override(self):
        c = classify_task("cualquier texto", explicit_route="DETERMINISTIC")
        self.assertEqual(c["route"], "DETERMINISTIC")


if __name__ == "__main__":
    unittest.main()
