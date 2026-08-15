"""VG-02 tests — RouterHTTPGateway without live network."""
import os
import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow_kernel.gateway.router_http import RouterHTTPGateway, build_gateway_from_env
from wordflow_kernel.gateway.intelligence import make_request, MockIntelligenceGateway


class TestRouterHTTP(unittest.TestCase):
    def test_empty_url_deny(self):
        gw = RouterHTTPGateway(router_url="", allow_mock_fallback=False)
        res = gw.execute(make_request("T1", "llm.complete", {}))
        self.assertEqual(res.status, "DENY")
        self.assertEqual(res.output.get("reason"), "ROUTER_URL_empty")

    def test_empty_url_mock_fallback(self):
        gw = RouterHTTPGateway(router_url="", allow_mock_fallback=True)
        res = gw.execute(make_request("T2", "llm.complete", {}))
        self.assertEqual(res.status, "MOCK")

    def test_build_from_env_mock(self):
        with patch.dict(os.environ, {"ROUTER_URL": ""}, clear=False):
            os.environ.pop("ROUTER_URL", None)
            gw = build_gateway_from_env()
            self.assertIsInstance(gw, MockIntelligenceGateway)

    def test_build_from_env_http(self):
        with patch.dict(os.environ, {"ROUTER_URL": "http://127.0.0.1:9999"}):
            gw = build_gateway_from_env()
            self.assertIsInstance(gw, RouterHTTPGateway)

    def test_success_parse(self):
        gw = RouterHTTPGateway(router_url="http://example.test")
        fake_resp = MagicMock()
        fake_resp.read.return_value = b'{"status":"OK","output":{"text":"hi"},"provider":"grok","request_id":"R1"}'
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = lambda *a: None
        with patch("urllib.request.urlopen", return_value=fake_resp):
            res = gw.execute(make_request("T3", "llm.complete", {"messages": []}))
        self.assertEqual(res.status, "OK")
        self.assertEqual(res.output.get("text"), "hi")
        self.assertEqual(res.provider, "grok")


if __name__ == "__main__":
    unittest.main()
