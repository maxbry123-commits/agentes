 cat /root/.openclaw/chat_injector.py 2>/dev/null
import os, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

OPENCLAW_URL = "http://127.0.0.1:18789"
INJECTOR_PORT = int(os.environ.get("INJECTOR_PORT", "18793"))
DEFAULT_TOKEN = "${OC_GATEWAY_TOKEN}"

INJECT_HTML = "<!DOCTYPE html><html><head><meta charset=\"utf-8\"><title>Cargando OpenClaw</title><script>(function(){var o=window.location.origin;var w=o.replace(/^http/,'ws')+'/';var t=new URLSearchParams(window.location.search).get('token')||'__TOKEN__';localStorage.setItem('openclaw.control.settings.v1',JSON.stringify({gateway:{url:w,token:t},theme:'claw',themeMode:'dark'}));localStorage.setItem('openclaw.control.currentGateway.v1',JSON.stringify({url:w,token:t}));window.location.replace(o+'/chat?session=main&token='+t);})();</script></head><body style=\"background:#000;color:#fff;font-family:system-ui;display:flex;align-items:center;justify-content:center;height:100vh;margin:0\"><div style=\"text-align:center\"><div style=\"font-size:32px;margin-bottom:12px\">⚡</div><div>Cargando OpenClaw...</div></div></body></html>"

class InjectorHandler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _proxy_openclaw(self, p):
        try:
            req = urllib.request.Request(f"{OPENCLAW_URL}{p}", method=self.command)
            for k,v in self.headers.items():
                if k.lower() not in ("host","content-length","connection"):
                    req.add_header(k, v)
            cl = int(self.headers.get("Content-Length", 0))
            if cl: req.data = self.rfile.read(cl)
            with urllib.request.urlopen(req, timeout=15) as resp:
                self.send_response(resp.status)
                ct = resp.headers.get("Content-Type", "")
                body = resp.read()
                if "text/html" in ct and b"</head>" in body:
                    bs = body.decode("utf-8", errors="ignore")
                    inject = INJECT_HTML.replace("__TOKEN__", DEFAULT_TOKEN)
                    bs = bs.replace("</head>", inject + "</head>", 1)
                    body = bs.encode()
                self.send_header("Content-Type", ct)
                self.send_header("Content-Length", str(len(body)))
                for k,v in resp.headers.items():
                    if k.lower() not in ("transfer-encoding","content-encoding","content-length","connection"):
                        self.send_header(k, v)
                self.end_headers()
                self.wfile.write(body)
        except Exception as e:
            self.send_response(502); self.send_header("Content-Type","text/plain"); self.end_headers()
            self.wfile.write(f"openclaw proxy error: {e}".encode())
    def do_GET(self):
        from urllib.parse import urlparse
        parsed = urlparse(self.path)
        if parsed.path in ("/","/index.html"):
            html = INJECT_HTML.replace("__TOKEN__", DEFAULT_TOKEN)
            self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Content-Length", str(len(html))); self.end_headers(); self.wfile.write(html.encode()); return
        self._proxy_openclaw(self.path)
    def do_POST(self): self._proxy_openclaw(self.path)

class ThreadedServer(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

if __name__ == "__main__":
    print(f"Chat injector :{INJECTOR_PORT}", flush=True)
    ThreadedServer(("0.0.0.0", INJECTOR_PORT), InjectorHandler).serve_forever()
root@vmi3428294:~# echo 