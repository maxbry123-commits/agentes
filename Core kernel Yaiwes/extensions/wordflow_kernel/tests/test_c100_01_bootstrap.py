# -*- coding: utf-8 -*-
"""C100-01 — bootstrap_v1 E2E Fake."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestC10001(unittest.TestCase):
    def test_bootstrap_full_fake(self):
        from wordflow_kernel.bootstrap_v1 import run_bootstrap_v1

        r = run_bootstrap_v1(
            "Construir extension kernel con tests deterministas y deploy Fake",
            run_loop=True,
            run_deploy=True,
        )
        self.assertTrue(r.ok, msg=str(r))
        self.assertEqual(r.llm_control, "DENY")
        self.assertTrue(r.code_path.get("ok"))
        self.assertTrue(r.loop.get("ok") or r.loop.get("skipped"))
        self.assertTrue(r.deploy.get("ok") or r.deploy.get("skipped"))

    def test_empty_input(self):
        from wordflow_kernel.bootstrap_v1 import run_bootstrap_v1

        r = run_bootstrap_v1("")
        self.assertFalse(r.ok)
        self.assertEqual(r.stage, "input")


if __name__ == "__main__":
    unittest.main()
