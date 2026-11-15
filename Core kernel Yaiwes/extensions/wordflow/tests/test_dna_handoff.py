# -*- coding: utf-8 -*-
"""Tests T42 DNA handoff."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.dna_handoff import accept_dna_handoff, build_dna_handoff
from extensions.wordflow.engine.loop_bridge import bridge_to_lock


class TestDnaHandoff(unittest.TestCase):
    def test_roundtrip(self):
        lock = bridge_to_lock(
            "objective: dna handoff\nsuccess: accept\nconstraint: 0% LLM\n"
        )["lock"]
        pkg = build_dna_handoff(lock, policies={"llm": "DENY"})
        self.assertTrue(pkg["ok"])
        acc = accept_dna_handoff(pkg)
        self.assertTrue(acc["ok"])

    def test_tamper_reject(self):
        lock = bridge_to_lock("objective: tamper handoff\nsuccess: deny\n")["lock"]
        pkg = build_dna_handoff(lock)
        pkg["dna"]["objectives"] = ["mutated"]
        acc = accept_dna_handoff(pkg)
        self.assertFalse(acc["ok"])


if __name__ == "__main__":
    unittest.main()
