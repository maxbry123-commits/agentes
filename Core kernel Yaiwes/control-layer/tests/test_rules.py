# -*- coding: utf-8 -*-
"""tests/test_rules.py — A3"""
from __future__ import annotations
import sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from control.fingerprint import build_fingerprint
from control.rules import load_routing, load_bundles, op_type_from_fingerprint, select_contracts

class TestRules(unittest.TestCase):
    def test_routing_seed(self):
        rt = load_routing()
        for k in ("READ_LOCAL", "WRITE_LOCAL", "NETWORK_CALL", "LLM_CALL", "MOUNT_EXTENSION"):
            self.assertIn(k, rt)
            self.assertTrue(len(rt[k]) >= 1)

    def test_bundles_seed(self):
        bd = load_bundles()
        self.assertIn("security.bundle", bd)
        self.assertIn("runtime.bundle", bd)

    def test_read_select(self):
        fp = build_fingerprint("read local config list")
        cs = select_contracts(fp)
        self.assertIn("C03", cs)
        self.assertIn("C28", cs)

    def test_write_secret_adds_security(self):
        fp = build_fingerprint("install package token secret")
        cs = select_contracts(fp)
        self.assertIn("C47", cs)
        self.assertIn("C45", cs)

    def test_determinism(self):
        fp = build_fingerprint("https://api.example.com fetch")
        self.assertEqual(select_contracts(fp), select_contracts(fp))

    def test_mount_op(self):
        fp = build_fingerprint("mount load_extension")
        self.assertEqual(op_type_from_fingerprint(fp), "MOUNT_EXTENSION")
        cs = select_contracts(fp)
        self.assertIn("C82", cs)

if __name__ == "__main__":
    unittest.main(verbosity=2)
