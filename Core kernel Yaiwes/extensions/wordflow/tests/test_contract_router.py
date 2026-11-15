# -*- coding: utf-8 -*-
"""Tests D7 ContractRouter 13 types."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.contract_router import DEFAULT_ROUTING, ContractRouter


class TestContractRouter(unittest.TestCase):
    def test_13_types(self):
        self.assertEqual(len(DEFAULT_ROUTING), 13)
        r = ContractRouter(routing=dict(DEFAULT_ROUTING))
        self.assertTrue(r.assert_13()["ok"])

    def test_select_git(self):
        r = ContractRouter(routing=dict(DEFAULT_ROUTING))
        s = r.select("GIT_OP")
        self.assertTrue(s["ok"])
        self.assertIn("C00", s["contracts"])
        self.assertIn("C82", s["contracts"])

    def test_unknown(self):
        r = ContractRouter(routing=dict(DEFAULT_ROUTING))
        s = r.select("MAGIC")
        self.assertFalse(s["ok"])


if __name__ == "__main__":
    unittest.main()
