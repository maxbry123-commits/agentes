# -*- coding: utf-8 -*-
"""tests/test_fingerprint.py — A1"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from control.fingerprint import Fingerprint, build_fingerprint, fingerprint_from_dict


class TestFingerprint(unittest.TestCase):
    def test_install_write_network(self):
        fp = build_fingerprint("install package from https://pypi.org with token")
        self.assertEqual(fp.action, "install")
        self.assertTrue(fp.writes)
        self.assertTrue(fp.network)
        self.assertTrue(fp.credentials)
        self.assertTrue(fp.external)

    def test_delete_irreversible(self):
        fp = build_fingerprint("delete force drop table")
        self.assertEqual(fp.action, "delete")
        self.assertTrue(fp.irreversible)

    def test_read_local(self):
        fp = build_fingerprint("read local config file list show")
        self.assertEqual(fp.action, "read")
        self.assertFalse(fp.writes)
        self.assertFalse(fp.network)

    def test_determinism_same_hash(self):
        a = build_fingerprint("install npm package")
        b = build_fingerprint("install npm package")
        self.assertEqual(a.hash(), b.hash())
        self.assertEqual(a.to_dict(), b.to_dict())

    def test_empty_unknown(self):
        fp = build_fingerprint("")
        self.assertEqual(fp.action, "unknown")
        self.assertFalse(fp.writes)

    def test_dict_input(self):
        fp = build_fingerprint({"op": "push", "url": "https://github.com/x/y", "token": "x"})
        self.assertTrue(fp.network)
        self.assertTrue(fp.credentials)

    def test_from_dict_roundtrip(self):
        fp = build_fingerprint("mount extension parallel")
        fp2 = fingerprint_from_dict(fp.to_dict())
        self.assertEqual(fp, fp2)
        self.assertTrue(fp2.parallel)

    def test_frozen(self):
        fp = build_fingerprint("read")
        with self.assertRaises(Exception):
            fp.writes = True  # type: ignore


if __name__ == "__main__":
    unittest.main(verbosity=2)
