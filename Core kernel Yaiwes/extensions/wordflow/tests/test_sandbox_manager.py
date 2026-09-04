# -*- coding: utf-8 -*-
"""Tests T16 SandboxManager."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.sandbox_manager import SandboxError, SandboxManager


class TestSandboxManager(unittest.TestCase):
    def test_allocate_release(self):
        m = SandboxManager(n_slots=2)
        self.assertEqual(len(m.list_free()), 2)
        a = m.allocate("task_1")
        self.assertEqual(a["status"], "ALLOCATED")
        self.assertEqual(len(m.list_free()), 1)
        m.mark_running(a["sandbox_id"])
        m.release(a["sandbox_id"])
        self.assertEqual(len(m.list_free()), 2)

    def test_no_free(self):
        m = SandboxManager(n_slots=1)
        m.allocate("t1")
        with self.assertRaises(SandboxError):
            m.allocate("t2")

    def test_error_recover(self):
        m = SandboxManager(n_slots=1)
        a = m.allocate("t")
        m.mark_error(a["sandbox_id"])
        self.assertEqual(m.snapshot()["by_status"].get("ERROR"), 1)
        m.recover_error(a["sandbox_id"])
        self.assertEqual(len(m.list_free()), 1)

    def test_backend_effective_logical(self):
        m = SandboxManager(n_slots=1, backend="docker")
        snap = m.snapshot()
        self.assertEqual(snap["backend_effective"], "logical")


if __name__ == "__main__":
    unittest.main()
