 cat /root/.openclaw/final_loader.py 2>/dev/null
"""Loader FINAL: usa POSTMESSAGE desde el parent al iframe para escribir localStorage."""
import os, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

OPENCLAW_URL = "http://127.0.0.1:18789"
FINAL_PORT = int(os.environ.get("FINAL_PORT", "18795"))
TOKEN = "${OC_GATEWAY_TOKEN}"

# Usamos un iframe con srcdoc que carga el openclaw via postMessage
LOADER_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>OpenClaw</title>
<style>
body{margin:0;background:#000;color:#fff;font-family:system-ui;display:flex;align-items:center;justify-content:center;height:100vh}
iframe{width:100%;height:100vh;border:0}
</style>
</head>
<body>
<iframe id="f"></iframe>
<script>
const TOKEN = '""" + TOKEN + """';
const WSPORT = (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/';
const settings = { gateway: { url: WSPORT, token: TOKEN }, theme: 'claw', themeMode: 'dark' };
const gwSettings = { url: WSPORT, token: TOKEN };

// Cargar el openclaw en el iframe, PERO antes escribir localStorage via sessionStorage del parent
// (esto solo funciona si es mismo origin, así que lo hacemos via document.cookie)
document.cookie = 'openclaw_settings=' + encodeURIComponent(JSON.stringify(settings)) + '; path=/';

// Cargar iframe directamente al openclaw oficial
document.getElementById('f').src = location.protocol + '//' + location.host + '/?token=' + TOKEN;
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(LOADER_HTML)))
        self.end_headers()
        self.wfile.write(LOADER_HTML.encode())


class ThreadedServer(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    print(f"Final loader :{FINAL_PORT}", flush=True)
    ThreadedServer(("0.0.0.0", FINAL_PORT), Handler).serve_forever()
root@vmi3428294:~# echo 