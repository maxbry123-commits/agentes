# -*- coding: utf-8 -*-
"""Tests V1-04 entrypoint_v1."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.entrypoint_v1 import reset_default, run_v1
from extensions.wordflow.engine.orchestrator_v1 import OrchestratorV1


class TestEntrypointV1(unittest.TestCase):
    def setUp(self):
        reset_default()

    def test_run_v1_happy(self):
        r = run_v1(
            "crear validacion determinista",
            topic="validacion",
            operation="READ_LOCAL",
            risk_score=1,
            band="low",
            orchestrator=OrchestratorV1(),
        )
        self.assertIn("ok", r)
        self.assertIn("stage", r)

    def test_run_v1_bad_op(self):
        r = run_v1("x", operation="ZZZ", orchestrator=OrchestratorV1())
        self.assertFalse(r["ok"])


if __name__ == "__main__":
    unittest.main()
