"""Integration contract test for the Wordflow → OpenClaw cable.

Uses a local HTTP server; no external secret or live service is required.
"""
import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wordflow_kernel.engines.openclaw_stub import OpenClawEngine
from wordflow_kernel.engines.port import EngineRequest
from wordflow_kernel.gateway.openclaw_http import OpenClawHTTPGateway


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        size = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(size))
        assert body["model"] == "openclaw/default"
        assert body["messages"][0]["content"] == "hello"
        raw = json.dumps({"id": "local-test", "choices": [{"message": {"content": "OPENCLAW_CABLE_OK"}}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *_args):
        return


class TestOpenClawCable(unittest.TestCase):
    def test_engine_uses_openclaw_gateway_contract(self):
        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            gateway = OpenClawHTTPGateway(f"http://127.0.0.1:{server.server_port}", "local-test-token")
            request = EngineRequest("TASK-G7", "TRACE-G7", [{"role": "user", "content": "hello"}])
            result = OpenClawEngine().reason(request, gateway)
            self.assertEqual(result.status, "OK")
            self.assertEqual(result.content, "OPENCLAW_CABLE_OK")
            self.assertEqual(result.meta["provider"], "openclaw")
        finally:
            server.shutdown()
            thread.join(timeout=2)

    def test_gateway_fails_closed(self):
        gateway = OpenClawHTTPGateway("", "")
        request = EngineRequest("TASK-G7-DENY", "TRACE-G7-DENY", [{"role": "user", "content": "hello"}])
        result = OpenClawEngine().reason(request, gateway)
        self.assertEqual(result.status, "DENY")


if __name__ == "__main__":
    unittest.main()
