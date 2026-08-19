# -*- coding: utf-8 -*-
"""KernelExtMotor dispatch ingest → kernel reception."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestKernelExtMotorReception(unittest.TestCase):
    def test_dispatch_ingest(self):
        from wordflow.motors.kernel_ext.motor import KernelExtMotor

        motor = KernelExtMotor()
        out = motor.dispatch(
            "ingest",
            {"raw_text": "objective: motor link\nsuccess: ok"},
        )
        self.assertEqual(out.get("status"), "OK")
        result = out.get("result") or {}
        self.assertTrue(result.get("invoked", {}).get("input_compiler"))

    def test_reception_link_has_locate(self):
        from wordflow.motors.kernel_ext.motor import KernelExtMotor

        motor = KernelExtMotor()
        out = motor.dispatch("reception_link", {"repo": "agentes"})
        self.assertEqual(out.get("status"), "OK")
        self.assertIn("github.com", out.get("link", ""))
        self.assertIn("locate", out)


if __name__ == "__main__":
    unittest.main()
