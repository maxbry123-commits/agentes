 cat /root/.openclaw/mcp_bridge.py
#!/usr/bin/env python3
"""MCP/API Bridge para OpenClaw. Conecta cosas al openclaw :18789 SIN TOCARLO."""
import os, json, time, uuid, threading, base64, struct
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from datetime import datetime, timezone

OPENCLAW_WS = "127.0.0.1"
OPENCLAW_PORT = 18789
OPENCLAW_TOKEN = "${OC_GATEWAY_TOKEN}"
ANCHORS_DIR = "/root/.openclaw/anchors"
SKILLS_DIR = "/root/.openclaw/skills"
MCP_PORT = int(os.environ.get("MCP_PORT", "18791"))
MCP_LOG = "/var/log/mcp-bridge.log"

os.makedirs(os.path.join(ANCHORS_DIR, "documents"), exist_ok=True)
os.makedirs(os.path.join(ANCHORS_DIR, "skills"), exist_ok=True)
os.makedirs(SKILLS_DIR, exist_ok=True)


def log(msg):
    line = f"[{datetime.now(timezone.utc).isoformat()}] {msg}"
    print(line, flush=True)
    try:
        with open(MCP_LOG, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


class OpenClawWS:
    def __init__(self):
        self.sock = None
        self.lock = threading.Lock()
        self.connect()

    def connect(self):
        import socket as sk
        s = sk.create_connection((OPENCLAW_WS, OPENCLAW_PORT), timeout=10)
        key = base64.b64encode(os.urandom(16)).decode()
        s.send(f"GET / HTTP/1.1\r\nHost: {OPENCLAW_WS}:{OPENCLAW_PORT}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\nAuthorization: Bearer {OPENCLAW_TOKEN}\r\nOrigin: http://127.0.0.1:18789\r\n\r\n".encode())
        buf = b""
        while b"connect.challenge" not in buf:
            try: c = s.recv(4096)
            except: break
            if not c: break
            buf += c
        hdr_end = buf.find(b"\r\n\r\n") + 4
        ws = buf[hdr_end:]
        plen = ws[1] & 0x7F
        if plen == 126: plen = struct.unpack("!H", ws[2:4])[0]; start = 4
        else: start = 2
        json.loads(ws[start:start+plen].decode())
        self.sock = s
        self._send_frame(json.dumps({"type":"req","id":"c-bridge","method":"connect","params":{"minProtocol":1,"maxProtocol":10,"auth":{"token":OPENCLAW_TOKEN},"client":{"id":"openclaw-control-ui","version":"2026.6.11","platform":"web","mode":"ui"},"scopes":["operator.read","operator.write","operator.admin"]}}))
        # ESPERAR el hello-ok antes de retornar
        start = time.time()
        hello_ok = False
        while time.time() - start < 5:
            r = self._read_frame(timeout=2)
            if not r: continue
            if r.get("id") == "c-bridge" and r.get("ok"):
                hello_ok = True
                break
            if r.get("type") == "event": continue
        if not hello_ok:
            log("WARN: no se recibio hello-ok de openclaw")
        # drena eventos iniciales (health/tick)
        for _ in range(3):
            try: r = self._read_frame(timeout=1)
            except: break
        log(f"MCP bridge conectado a openclaw :18789 via WebSocket (hello_ok={hello_ok})")

    def _send_frame(self, msg):
        data = msg.encode()
        plen = len(data)
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i%4] for i,b in enumerate(data))
        if plen < 126: h = bytes([0x81, plen | 0x80]) + mask
        elif plen < 65536: h = bytes([0x81, 126 | 0x80]) + struct.pack("!H", plen) + mask
        else: h = bytes([0x81, 127 | 0x80]) + struct.pack("!Q", plen) + mask
        self.sock.send(h + masked)

    def _read_frame(self, timeout=5):
        self.sock.settimeout(timeout)
        h = self.sock.recv(2)
        if len(h) < 2: return None
        plen = h[1] & 0x7F
        if plen == 126: plen = struct.unpack("!H", self.sock.recv(2))[0]
        elif plen == 127: plen = struct.unpack("!Q", self.sock.recv(8))[0]
        payload = b""
        while len(payload) < plen:
            try: c = self.sock.recv(plen - len(payload))
            except: break
            if not c: break
            payload += c
        if (h[0] & 0x0F) == 0x1:
            try: return json.loads(payload.decode())
            except: return None
        return None

    def call(self, method, params=None, timeout=10):
        with self.lock:
            try:
                if self.sock is None: self.connect()
                req_id = uuid.uuid4().hex[:8]
                log(f"call {method} id={req_id}")
                self._send_frame(json.dumps({"type":"req","id":req_id,"method":method,"params":params or {}}))
                start = time.time()
                count = 0
                while time.time() - start < timeout:
                    r = self._read_frame(timeout=2)
                    if not r:
                        count += 1
                        continue
                    rtype = r.get("type")
                    rid = r.get("id")
                    if rtype == "event":
                        log(f"  skip event: {r.get("event")}")
                        continue
                    log(f"  got: type={rtype} id={rid} ok={r.get("ok")}")
                    if rid == req_id: return r
                log(f"  TIMEOUT after {count} empty reads")
                return {"ok": False, "error": "timeout"}
            except Exception as e:
                log(f"WS call error: {e}")
                try: self.sock.close()
                except: pass
                self.sock = None
                return {"ok": False, "error": str(e)}


ws_client = None
def get_ws():
    global ws_client
    if ws_client is None:
        ws_client = OpenClawWS()
    return ws_client


class MCPHandler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _ok(self, body):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, indent=2, default=str)
        body = body.encode() if isinstance(body, str) else body
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _err(self, code, msg):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": msg}).encode())

    def _read_body(self):
        cl = int(self.headers.get("Content-Length", 0))
        if cl: return json.loads(self.rfile.read(cl).decode())
        return {}

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/mcp/health":
            try:
                ws = get_ws()
                return self._ok({"status":"ok","openclaw_connected": ws.sock is not None,
                    "endpoints":["/mcp/health","/mcp/models","/mcp/sessions","/mcp/anchor","/mcp/send","/mcp/skill","/mcp/list"]})
            except Exception as e:
                return self._err(503, str(e))
        if path == "/mcp/models":
            return self._ok(get_ws().call("models.list", {}))
        if path == "/mcp/sessions":
            return self._ok(get_ws().call("sessions.list", {}))
        if path == "/mcp/list":
            docs = []
            for d in [os.path.join(ANCHORS_DIR, "documents"), os.path.join(ANCHORS_DIR, "skills")]:
                if os.path.isdir(d):
                    for f in sorted(os.listdir(d)):
                        p = os.path.join(d, f)
                        if os.path.isfile(p):
                            docs.append({"name": f, "kind": "document" if "documents" in d else "skill", "size": os.path.getsize(p), "path": p})
            return self._ok({"anchors": docs})
        if path == "/" or path == "/index.html":
            try:
                with open("/root/.openclaw/mcp_index.html") as f: body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body.encode())))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body.encode())
                return
            except Exception as e: return self._err(500, str(e))
        self._err(404, f"unknown: {path}")

    def do_POST(self):
        path = self.path.split("?")[0]
        body = self._read_body()
        if path == "/mcp/anchor":
            kind = body.get("kind", "document")
            title = body.get("title", "untitled")
            content = body.get("content", "")
            anchor_id = uuid.uuid4().hex[:8]
            subdir = "documents" if kind == "document" else "skills"
            full = os.path.join(ANCHORS_DIR, subdir, f"{anchor_id}.md")
            with open(full, "w") as f: f.write(f"# {title}\n\n{content}\n")
            os.chmod(full, 0o600)
            log(f"anchor guardado: {full}")
            return self._ok({"ok": True, "id": anchor_id, "path": full, "kind": kind, "title": title})
        if path == "/mcp/send":
            message = body.get("message", "")
            session = body.get("session", "agent:main:main")
            if not message: return self._err(400, "no message")
            return self._ok(get_ws().call("chat.send", {"idempotencyKey": uuid.uuid4().hex, "sessionKey": session, "message": message}, timeout=30))
        if path == "/mcp/skill":
            name = body.get("name", "skill")
            content = body.get("content", "")
            path_full = os.path.join(SKILLS_DIR, f"{name}.md")
            with open(path_full, "w") as f: f.write(content)
            os.chmod(path_full, 0o600)
            return self._ok({"ok": True, "path": path_full})
        self._err(404, f"unknown: {path}")


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    log(f"MCP bridge arrancando en :{MCP_PORT}")
    try: get_ws()
    except Exception as e: log(f"WARN pre-connect: {e}")
    srv = ThreadedHTTPServer(("0.0.0.0", MCP_PORT), MCPHandler)
    log(f"MCP bridge LISTO en :{MCP_PORT}")
    srv.serve_forever()
root@vmi3428294:~# echo 