"""VR-03 — UI gateway stub + wired kernel path."""
import json
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow_kernel.ui_gateway import UIGatewayPlugin, UIMessage


class TestVR03(unittest.TestCase):
    def test_ack(self):
        p = UIGatewayPlugin(wire_kernel=False)
        r = p.handle(UIMessage("s1", "hello"))
        self.assertEqual(r.status, "ACK")
        self.assertEqual(p.health()["messages"], 1)

    def test_wired_status(self):
        p = UIGatewayPlugin(wire_kernel=True)
        r = p.handle(UIMessage("s1", "objective: ui wired\nsuccess: kernel hop"))
        self.assertIn(r.status, ("ROUTED", "PARTIAL", "BLOCK"))
        self.assertEqual(r.detail.get("llm_control"), "DENY")

    def test_ficha(self):
        f = Path(__file__).resolve().parents[1] / "ui_gateway" / "ficha.v2.json"
        data = json.loads(f.read_text(encoding="utf-8"))
        self.assertEqual(data["llm_control"], "DENY")


if __name__ == "__main__":
    unittest.main()
