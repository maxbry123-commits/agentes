"""VG-03 tests — EnginePort OpenClaw/Hermes via Mock gateway."""
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow_kernel.gateway import MockIntelligenceGateway
from wordflow_kernel.engines import (
    EngineRegistry,
    EngineRequest,
    OpenClawEngine,
    HermesEngine,
)


class TestEngines(unittest.TestCase):
    def setUp(self):
        self.gw = MockIntelligenceGateway(fixed_text="REASONED")
        self.reg = EngineRegistry()
        self.reg.register(OpenClawEngine())
        self.reg.register(HermesEngine())

    def _req(self):
        return EngineRequest(
            task_id="TASK-R1",
            trace_id="TRACE-1",
            messages=[{"role": "user", "content": "plan"}],
            policy={"max_cost": 0.01},
            context={"goal": "x"},
        )

    def test_list_engines(self):
        self.assertEqual(self.reg.list_ids(), ["hermes", "openclaw"])

    def test_openclaw_via_mock(self):
        res = self.reg.reason("openclaw", self._req(), self.gw)
        self.assertEqual(res.engine_id, "openclaw")
        self.assertEqual(res.status, "STUB")
        self.assertEqual(res.content, "REASONED")

    def test_hermes_via_mock(self):
        res = self.reg.reason("hermes", self._req(), self.gw)
        self.assertEqual(res.engine_id, "hermes")
        self.assertEqual(res.content, "REASONED")

    def test_unknown_engine_deny(self):
        res = self.reg.reason("unknown", self._req(), self.gw)
        self.assertEqual(res.status, "DENY")


if __name__ == "__main__":
    unittest.main()
