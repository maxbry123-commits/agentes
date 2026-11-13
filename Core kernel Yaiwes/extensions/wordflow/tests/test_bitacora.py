# -*- coding: utf-8 -*-
"""Tests T0h Bitacora EventStore."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from extensions.wordflow.engine.bitacora import BitacoraStore, GENESIS_PREV


class TestBitacora(unittest.TestCase):
    def test_append_chain(self):
        store = BitacoraStore()
        e1 = store.append("LOCK_CREATED", "gl_1", {"objective": "x"})
        e2 = store.append("PING", "gl_1", {"action": "CONTINUE"})
        self.assertEqual(e1["seq"], 1)
        self.assertEqual(e1["prev_hash"], GENESIS_PREV)
        self.assertEqual(e2["seq"], 2)
        self.assertEqual(e2["prev_hash"], e1["event_hash"])
        self.assertTrue(store.verify_chain()["ok"])

    def test_no_rewrite(self):
        store = BitacoraStore()
        store.append("NOTE", "gl_1", {"msg": "a"})
        with self.assertRaises(RuntimeError):
            store.rewrite_forbidden()

    def test_persist_jsonl(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bitacora.jsonl"
            s1 = BitacoraStore(path)
            s1.append("STEP", "gl_x", {"step": "1"})
            s1.append("TOOL", "gl_x", {"tool": "t"})
            s2 = BitacoraStore(path)
            self.assertEqual(s2.length, 2)
            self.assertTrue(s2.verify_chain()["ok"])

    def test_filter(self):
        store = BitacoraStore()
        store.append("PING", "gl_a", {})
        store.append("FOCUS", "gl_b", {})
        store.append("PING", "gl_a", {})
        self.assertEqual(len(store.list_events(lock_id="gl_a")), 2)
        self.assertEqual(len(store.list_events(kind="FOCUS")), 1)

    def test_tamper_detected(self):
        store = BitacoraStore()
        store.append("NOTE", "gl_1", {"v": 1})
        store._events[0]["payload"] = {"v": 99}
        self.assertFalse(store.verify_chain()["ok"])


if __name__ == "__main__":
    unittest.main()
