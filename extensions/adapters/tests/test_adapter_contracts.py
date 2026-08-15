# -*- coding: utf-8 -*-
"""Tests C-28 Adapter contracts — offline, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.adapters.contracts import (
    AdapterError,
    CapabilityAdapter,
    EngineAdapter,
    StaticCapabilityAdapter,
    StaticEngineAdapter,
    validate_capability_result,
    validate_engine_result,
)


class TestAdapterContracts(unittest.TestCase):
    def test_static_capability(self):
        ad = StaticCapabilityAdapter("cap.github", "deploy.repository")
        self.assertIsInstance(ad, CapabilityAdapter)
        r = ad.invoke({"repo": "x/y"})
        self.assertTrue(r["ok"])
        self.assertEqual(r["llm_control"], "DENY")

    def test_static_engine(self):
        eng = StaticEngineAdapter("engine.stub", "code")
        self.assertIsInstance(eng, EngineAdapter)
        r = eng.execute({"task_id": "T_00"})
        self.assertTrue(r["ok"])
        self.assertEqual(r["status"], "SUCCESS")

    def test_bad_engine_status(self):
        with self.assertRaises(AdapterError):
            validate_engine_result({"ok": True, "status": "WEIRD"})

    def test_cap_missing_ok(self):
        with self.assertRaises(AdapterError):
            validate_capability_result({"data": {}})


if __name__ == "__main__":
    unittest.main()
