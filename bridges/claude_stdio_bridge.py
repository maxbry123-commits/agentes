 <sal/orchestrator/claude_stdio_bridge.py 2>/dev/null
#!/usr/bin/env python3
"""claude_stdio_bridge.py — Conecta a los 3 claude stdio (sonnet/opus/fable)
via sus PTY, expone HTTP en el orquestador para mandar tareas.
"""
import os, sys, time, json, threading, subprocess, fcntl, termios, struct, select, logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LOG = "/var/log/claude-stdio-bridge.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOG), logging.StreamHandler()],
)
log = logging.getLogger("claude-stdio-bridge")

# Mapeo modelo -> pts
PTS_MAP = {
    "sonnet": "/dev/pts/2",
    "opus":   "/dev/pts/3",
    "fable":  "/dev/pts/4",
}

class ClaudePTY:
    """Maneja un PTY con un claude stdio: lee su output, permite enviar input."""

    def __init__(self, name, pts_path):
        self.name = name
        self.pts_path = pts_path
        self.lock = threading.Lock()
        self.last_output = b""
        self.last_output_ts = 0
        self.busy = False
        self._stop = threading.Event()
        self._thread = None
        # abrir el path del PTY en modo rw (necesario root)
        try:
            self.fd = os.open(pts_path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
            log.info(f"[{name}] opened {pts_path} fd={self.fd}")
        except Exception as e:
            log.error(f"[{name}] no se pudo abrir {pts_path}: {e}")
            self.fd = None

    def start_reader(self):
        if self.fd is None: return
        self._thread = threading.Thread(target=self._reader_loop, daemon=True, name=f"reader-{self.name}")
        self._thread.start()

    def _reader_loop(self):
        while not self._stop.is_set():
            try:
                r, _, _ = select.select([self.fd], [], [], 0.5)
                if not r: continue
                try:
                    chunk = os.read(self.fd, 4096)
                    if chunk:
                        self.last_output += chunk
                        self.last_output_ts = time.time()
                        # mantener ultimos 8KB
                        if len(self.last_output) > 8192:
                            self.last_output = self.last_output[-8192:]
                except BlockingIOError:
                    pass
                except OSError as e:
                    if e.errno == 5:  # input/output error, PTY cerrado
                        log.warning(f"[{self.name}] PTY cerrado")
                        return
            except Exception as e:
                log.error(f"[{self.name}] reader error: {e}")
                time.sleep(1)

    def send(self, text, wait_seconds=20):
        """Envia text al PTY, espera wait_seconds por respuesta."""
        with self.lock:
            if self.fd is None:
                return {"ok": False, "error": f"pty_not_open: {self.pts_path}"}
            self.busy = True
            self.last_output = b""
            self.last_output_ts = time.time()
            try:
                # Enviar texto + Enter (\r)
                msg = text + "\r"
                os.write(self.fd, msg.encode("utf-8"))
            except Exception as e:
                self.busy = False
                return {"ok": False, "error": f"write_fail: {e}"}

        # Esperar output
        deadline = time.time() + wait_seconds
        prev_len = 0
        stable_count = 0
        while time.time() < deadline:
            time.sleep(0.3)
            with self.lock:
                cur_len = len(self.last_output)
                if cur_len > 0 and cur_len == prev_len:
                    stable_count += 1
                    if stable_count >= 2:  # 600ms sin cambios = listo
                        break
                else:
                    stable_count = 0
                prev_len = cur_len
        with self.lock:
            self.busy = False
            output = self.last_output.decode("utf-8", errors="replace")
            return {"ok": True, "output": output, "bytes": len(self.last_output)}

    def stop(self):
        self._stop.set()
        if self.fd is not None:
            try: os.close(self.fd)
            except: pass


bridges = {}
for name, pts in PTS_MAP.items():
    b = ClaudePTY(name, pts)
    b.start_reader()
    bridges[name] = b


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass
    def _json(self, code, obj):
        d = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(d)))
        self.end_headers()
        self.wfile.write(d)

    def _read_body(self):
        n = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(n) if n else b""

    def do_GET(self):
        if self.path == "/health":
            self._json(200, {n: {"busy": b.busy, "fd": b.fd is not None, "pts": b.pts_path, "last_bytes": len(b.last_output)} for n, b in bridges.items()})
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        try: body = json.loads(self._read_body() or b"{}")
        except: return self._json(400, {"error": "bad json"})
        if self.path.startswith("/claude/"):
            name = self.path.split("/")[-1]
            if name not in bridges:
                return self._json(404, {"error": f"unknown claude: {name}"})
            text = body.get("text") or body.get("message")
            if not text: return self._json(400, {"error": "missing text"})
            wait = int(body.get("wait_s", 25))
            r = bridges[name].send(text, wait_seconds=wait)
            return self._json(200, {"agent": name, **r})
        self._json(404, {"error": "not found"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "9092"))
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    log.info(f"claude-stdio-bridge HTTP on 127.0.0.1:{port} (POST /claude/sonnet|opus|fable)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        for b in bridges.values(): b.stop()
root@vmi3428294:~# echo 