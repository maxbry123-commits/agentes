# -*- coding: utf-8 -*-
"""Tests T39 Environment scan."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.environment_scan import scan_environment


class TestEnvironmentScan(unittest.TestCase):
    def test_scan_ok(self):
        r = scan_environment()
        self.assertTrue(r["ok"])
        self.assertIn("python", r["compute"])
        self.assertIn("local_runtime", r["capabilities"])

    def test_declared_services(self):
        r = scan_environment(declared_services={"huggingface": True})
        self.assertIn("hf_service", r["capabilities"])


if __name__ == "__main__":
    unittest.main()
