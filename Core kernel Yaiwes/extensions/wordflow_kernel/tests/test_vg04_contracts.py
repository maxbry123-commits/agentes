"""VG-04 — offline contract shapes Gateway + Engines + factory."""
import os
import unittest
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow_kernel.gateway import (
    MockIntelligenceGateway,
    RouterHTTPGateway,
    build_gateway_from_env,
    make_request,
)
from wordflow_kernel.engines import EngineRegistry, EngineRequest, OpenClawEngine, HermesEngine


class TestVG04Contracts(unittest.TestCase):
    def test_gateway_and_engine_chain(self):
        gw = MockIntelligenceGateway(fixed_text="CHAIN_OK")
        reg = EngineRegistry()
        reg.register(OpenClawEngine())
        reg.register(HermesEngine())
        req = EngineRequest(
            task_id="TASK-VG04",
            trace_id="TRACE-VG04",
            messages=[{"role": "user", "content": "x"}],
        )
        r1 = reg.reason("openclaw", req, gw)
        r2 = reg.reason("hermes", req, gw)
        self.assertEqual(r1.content, "CHAIN_OK")
        self.assertEqual(r2.content, "CHAIN_OK")
        self.assertGreaterEqual(len(gw.calls), 2)

    def test_factory_default_mock(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ROUTER_URL", None)
            gw = build_gateway_from_env()
            self.assertIsInstance(gw, MockIntelligenceGateway)

    def test_no_direct_vendor_in_request_body(self):
        req = make_request("T", "llm.complete", {"messages": []})
        body = req.to_router_body()
        blob = str(body).lower()
        self.assertNotIn("openai.com", blob)
        self.assertNotIn("api_key", blob)
        self.assertIn("task_id", body)
        self.assertIn("trace_id", body)

    def test_router_deny_without_url(self):
        gw = RouterHTTPGateway(router_url="", allow_mock_fallback=False)
        res = gw.execute(make_request("T", "llm.complete", {}))
        self.assertEqual(res.status, "DENY")


if __name__ == "__main__":
    unittest.main()
