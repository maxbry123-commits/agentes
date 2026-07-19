 <or-universal/orchestrator/openclaw_bridge_daemon.py
#!/usr/bin/env python3
"""openclaw_bridge_daemon.py v4 — una sola conexion WS, eventos indexados por idempotencyKey."""
import os, sys, time, json, logging, signal, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
sys.path.insert(0, "/opt/orquestador-universal")

LOG = "/var/log/openclaw-bridge.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOG), logging.StreamHandler()],
)
log = logging.getLogger("openclaw-bridge-daemon")

from orchestrator.openclaw_bridge import OpenClawBridge

br = OpenClawBridge(log=log)
br.start()
log.info(f"daemon v4 started, pid={os.getpid()}, log={LOG}")


class DaemonHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass
    def _read_body(self):
        n = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(n) if n else b""
    def _json(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            self._json(200 if br.connected else 503, {
                "status": "ok" if br.connected else "degraded",
                "connected": br.connected, "conn_id": br.conn_id,
            })
        elif self.path == "/spec":
            self._json(200, {"endpoints": ["GET /health", "GET /spec", "POST /request", "POST /chat"]})
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        try:
            body = json.loads(self._read_body() or b"{}")
        except Exception:
            return self._json(400, {"error": "bad json"})
        if self.path == "/chat":
            text = body.get("text") or body.get("message")
            if not text: return self._json(400, {"error": "missing text"})
            sk = body.get("session_key", "main")
            ts = int(body.get("timeout_s", 30))
            if not br.connected:
                return self._json(503, {"ok": False, "error": {"code": "BRIDGE_DOWN"}})
            idem = f"daemon-{int(time.time()*1000)}-{os.urandom(4).hex()}"
            r = br.request("chat.send", {
                "sessionKey": sk, "message": text, "idempotencyKey": idem,
            }, timeout=5)
            if not r.get("ok"):
                return self._json(200, r)
            run_id = r.get("payload", {}).get("runId")
            fr = br.wait_for_chat(idem, run_id=run_id, timeout=ts)
            return self._json(200, {
                "ok": fr.get("ok", False),
                "runId": run_id,
                "idempotencyKey": idem,
                "llm_response": fr.get("text"),
                "stop_reason": fr.get("stop_reason"),
                "content_chunks": fr.get("content_chunks"),
                "error": fr.get("error"),
            })
        if self.path == "/request":
            method = body.get("method")
            if not method: return self._json(400, {"error": "missing method"})
            r = br.request(method, body.get("params", {}), timeout=int(body.get("timeout", 30)))
            return self._json(200, r)
        self._json(404, {"error": "not found"})


httpd = ThreadingHTTPServer(("127.0.0.1", 9091), DaemonHandler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
log.info("daemon v4 HTTP on 127.0.0.1:9091 (POST /chat with idempotencyKey, POST /request)")


def shutdown(sig, frame):
    log.info(f"shutting down (sig={sig})")
    br.stop()
    httpd.shutdown()
    sys.exit(0)


signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)
while True:
    time.sleep(60)
    if not br.connected:
        log.warning("main bridge disconnected, will reconnect")
root@vmi3428294:~# echo 