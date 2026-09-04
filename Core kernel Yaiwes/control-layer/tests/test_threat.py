# -*- coding: utf-8 -*-
"""tests/test_threat.py — A2"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from control.fingerprint import build_fingerprint
from control.threat import analyze_threat, load_risk_matrix


class TestThreat(unittest.TestCase):
    def test_read_local_low(self):
        fp = build_fingerprint("read local config list show")
        t = analyze_threat(fp)
        self.assertLessEqual(t.risk_score, 3)
        self.assertEqual(t.band, "normal")

    def test_delete_secret_high(self):
        fp = build_fingerprint("delete force token secret https://api.example.com")
        t = analyze_threat(fp)
        self.assertGreaterEqual(t.risk_score, 8)
        self.assertEqual(t.band, "quarantine")

    def test_install_network_mid(self):
        fp = build_fingerprint("install package from https://pypi.org")
        t = analyze_threat(fp)
        self.assertGreaterEqual(t.risk_score, 4)
        self.assertIn(t.band, ("sheriff_check", "quarantine"))

    def test_determinism(self):
        fp = build_fingerprint("write file")
        a = analyze_threat(fp)
        b = analyze_threat(fp)
        self.assertEqual(a.to_dict(), b.to_dict())

    def test_matrix_loads(self):
        m = load_risk_matrix()
        self.assertIn("data", m)
        self.assertIn("operation", m)


if __name__ == "__main__":
    unittest.main(verbosity=2)
