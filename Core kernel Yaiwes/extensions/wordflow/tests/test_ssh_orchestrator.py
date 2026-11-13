# -*- coding: utf-8 -*-
"""Tests T20 SSHOrchestrator stub."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.ssh_orchestrator import (
    FakeSSHTransport,
    SSHError,
    SSHOrchestrator,
)


class TestSSHOrchestrator(unittest.TestCase):
    def test_fake_run(self):
        orch = SSHOrchestrator()
        r = orch.run_remote("vps1.example", "echo hi")
        self.assertTrue(r["ok"])
        self.assertIn("fake:echo hi", r["result"]["stdout"])

    def test_real_disabled(self):
        with self.assertRaises(SSHError):
            SSHOrchestrator(allow_real=True)

    def test_migrate_stub(self):
        orch = SSHOrchestrator()
        r = orch.migrate_task_stub("t1", "vps2", payload={"a": 1})
        self.assertEqual(r["mode"], "stub")
        self.assertEqual(r["task_id"], "t1")

    def test_history(self):
        fake = FakeSSHTransport()
        orch = SSHOrchestrator(transport=fake)
        orch.run_remote("h", "ls")
        ops = [h["op"] for h in fake.history]
        self.assertEqual(ops, ["connect", "exec", "close"])


if __name__ == "__main__":
    unittest.main()
