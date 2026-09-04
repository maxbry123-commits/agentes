"""R5 — three ops simulations. C100 remains False."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow_kernel.ops_sim import run_three, sim2_ui_agents
from wordflow_kernel.ui_gateway import UIGatewayPlugin, UIMessage


class TestOpsSim(unittest.TestCase):
    def test_sim2_agents_standalone(self):
        out = sim2_ui_agents()
        self.assertTrue(out["ok"])
        self.assertEqual(out["engines"]["openclaw"]["status"], "STUB")
        self.assertEqual(out["engines"]["hermes"]["status"], "STUB")
        self.assertFalse(out["vendor_call"])

    def test_ui_ack_opt_out(self):
        p = UIGatewayPlugin(wire_kernel=False)
        r = p.handle(UIMessage("s1", "hello"))
        self.assertEqual(r.status, "ACK")

    def test_ui_wired_invokes_agents(self):
        p = UIGatewayPlugin(wire_kernel=True)
        r = p.handle(UIMessage("s2", "objective: route\nsuccess: agents invoked"))
        self.assertIn(r.status, ("ROUTED", "PARTIAL", "BLOCK"))
        agents = (r.detail or {}).get("agents") or {}
        if isinstance(agents, dict) and "openclaw" in agents:
            self.assertTrue(agents["openclaw"].get("invoked"))

    def test_run_three_no_c100(self):
        report = run_three()
        self.assertFalse(report["c100"])
        self.assertEqual(len(report["sims"]), 3)
        self.assertTrue(any(s["id"] == "SIM-2" and s["ok"] for s in report["sims"]))


if __name__ == "__main__":
    unittest.main()
