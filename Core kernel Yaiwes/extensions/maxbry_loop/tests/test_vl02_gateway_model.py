"""VL-02 — GatewayModel uses IntelligenceGateway; no vendor URL in path."""
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from maxbry_loop.models import Goal, Task
from maxbry_loop.model import MockModel, GatewayModel, build_model
from wordflow_kernel.gateway import MockIntelligenceGateway


class TestVL02(unittest.TestCase):
    def test_mock_still_works(self):
        m = MockModel()
        t = Task(id="T1", title="a", description="b")
        r = m.execute(t, Goal(text="g"))
        self.assertEqual(r["status"], "done")

    def test_gateway_model_mock_backend(self):
        gw = MockIntelligenceGateway(fixed_text="VIA_GATEWAY")
        m = GatewayModel(gw)
        t = Task(id="T2", title="code", description="impl", acceptance=["tests"])
        r = m.execute(t, Goal(text="ship"))
        self.assertEqual(r["status"], "done")
        self.assertEqual(r["result"], "VIA_GATEWAY")
        self.assertTrue(any("gateway:MOCK" in e for e in r["evidence"]))
        self.assertEqual(len(gw.calls), 1)
        self.assertEqual(gw.calls[0].capability, "llm.complete")

    def test_build_model_default_mock(self):
        m = build_model({"model": {"provider": "mock"}})
        self.assertIsInstance(m, MockModel)

    def test_build_model_gateway(self):
        gw = MockIntelligenceGateway()
        m = build_model({"model": {"provider": "gateway"}}, gateway=gw)
        self.assertIsInstance(m, GatewayModel)

    def test_no_openai_import_in_model_module(self):
        import maxbry_loop.model as mod
        src = Path(mod.__file__).read_text(encoding="utf-8").lower()
        self.assertNotIn("openai", src)
        self.assertNotIn("anthropic", src)
        self.assertNotIn("api.openai.com", src)


if __name__ == "__main__":
    unittest.main()
