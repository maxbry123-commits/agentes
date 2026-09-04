import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXT = ROOT / "extensions"
if str(EXT) not in sys.path:
    sys.path.insert(0, str(EXT))

from openclaw_http_gateway import OpenClawHTTPGateway
from wordflow_kernel.gateway.intelligence import GatewayRequest


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        size = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(size))
        assert body["model"] == "openclaw/default"
        payload = {"id": "chatcmpl-test", "choices": [{"message": {"content": "REAL_ADAPTER_TEST"}}]}
        raw = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *_args):
        return


class TestOpenClawHTTPGateway(unittest.TestCase):
    def test_fail_closed_without_configuration(self):
        gateway = OpenClawHTTPGateway(base_url="", token="")
        response = gateway.execute(GatewayRequest("t1", "tr1", "llm.complete", {"messages": []}))
        self.assertEqual(response.status, "DENY")

    def test_real_http_contract(self):
        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            gateway = OpenClawHTTPGateway(base_url=f"http://127.0.0.1:{server.server_port}", token="test-token")
            response = gateway.execute(GatewayRequest(
                "t2", "tr2", "llm.complete", {"messages": [{"role": "user", "content": "hello"}]}
            ))
            self.assertEqual(response.status, "OK")
            self.assertEqual(response.provider, "openclaw")
            self.assertEqual(response.output["text"], "REAL_ADAPTER_TEST")
            self.assertTrue(response.evidence_hash)
        finally:
            server.shutdown()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
