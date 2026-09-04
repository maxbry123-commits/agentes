# -*- coding: utf-8 -*-
"""Tests C-13 input_quality_bar — offline, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.input_quality_bar import (
    QualityBarError,
    admit_or_reject,
    evaluate_input_quality,
)

GOOD = (
    "Objetivo: implementar el módulo de deploy determinista "
    "con expected_head y sin force_push para el Wordflow."
)


class TestQualityBar(unittest.TestCase):
    def test_good(self):
        r = evaluate_input_quality(GOOD)
        self.assertTrue(r["ok"])
        self.assertEqual(r["policy"], "never_mvp")

    def test_mvp_marker(self):
        with self.assertRaises(QualityBarError):
            evaluate_input_quality("Objetivo implementar algo MVP only please")

    def test_too_short(self):
        r = admit_or_reject("hi")
        self.assertFalse(r["ok"])
        self.assertIn("TOO_SHORT", r["reason_codes"])

    def test_empty(self):
        r = admit_or_reject("")
        self.assertIn("EMPTY_INPUT", r["reason_codes"])


if __name__ == "__main__":
    unittest.main()
