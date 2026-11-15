# -*- coding: utf-8 -*-
"""Tests T18 CheckpointStore."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from extensions.wordflow.engine.checkpoint_store import CheckpointStore


class TestCheckpointStore(unittest.TestCase):
    def test_save_restore(self):
        store = CheckpointStore()
        cp = store.save(
            lock_id="gl_1",
            task_id="t1",
            state={"step": 3, "note": "mid"},
            label="mid-run",
        )
        self.assertTrue(store.verify(cp)["ok"])
        r = store.restore(cp["checkpoint_id"])
        self.assertTrue(r["ok"])
        self.assertEqual(r["state"]["step"], 3)

    def test_tamper(self):
        store = CheckpointStore()
        cp = store.save(lock_id="gl", state={"a": 1})
        cp["state"] = {"a": 99}
        self.assertFalse(store.verify(cp)["ok"])

    def test_persist(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "cp.jsonl"
            s1 = CheckpointStore(path)
            cp = s1.save(lock_id="gl", state={"x": True})
            s2 = CheckpointStore(path)
            r = s2.restore(cp["checkpoint_id"])
            self.assertTrue(r["ok"])
            self.assertTrue(r["state"]["x"])

    def test_list_for_lock(self):
        store = CheckpointStore()
        store.save(lock_id="a", state={})
        store.save(lock_id="b", state={})
        store.save(lock_id="a", state={"n": 2})
        self.assertEqual(len(store.list_for_lock("a")), 2)


if __name__ == "__main__":
    unittest.main()
