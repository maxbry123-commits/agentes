# -*- coding: utf-8 -*-
"""Tests C-24 Ledger — offline, 0% LLM."""
from __future__ import annotations

import unittest

from extensions.wordflow.state.ledger import Ledger, LedgerError


class TestLedger(unittest.TestCase):
    def test_append_and_chain(self):
        lg = Ledger(mission_id="m1")
        lg.append("LOCK", {"id": "L1"})
        lg.append("PLAN", {"nodes": 3})
        v = lg.verify_chain()
        self.assertTrue(v["ok"])
        self.assertEqual(v["count"], 2)

    def test_tamper_breaks(self):
        lg = Ledger()
        lg.append("A", {})
        lg.append("B", {})
        lg._entries[1]["payload"]["x"] = 1  # intentional tamper
        self.assertFalse(lg.verify_chain()["ok"])

    def test_empty_kind(self):
        lg = Ledger()
        with self.assertRaises(LedgerError):
            lg.append("", {})


if __name__ == "__main__":
    unittest.main()
