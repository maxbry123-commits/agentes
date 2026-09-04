# -*- coding: utf-8 -*-
"""Tests V1-06 public API exports."""
from __future__ import annotations

import unittest


class TestPublicAPIV1(unittest.TestCase):
    def test_imports(self):
        from extensions.wordflow.engine import (
            BitacoraStore,
            ContractRouter,
            OrchestratorV1,
            RecoveryEngine,
            compile_dna,
            gate_c00,
            run_v1,
        )

        self.assertTrue(callable(run_v1))
        self.assertTrue(callable(gate_c00))
        self.assertTrue(callable(compile_dna))
        self.assertIsNotNone(OrchestratorV1)
        self.assertIsNotNone(ContractRouter)
        self.assertIsNotNone(BitacoraStore)
        self.assertIsNotNone(RecoveryEngine)


if __name__ == "__main__":
    unittest.main()
