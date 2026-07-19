"""
test_post.py — Test del orquestador desde el VPS.
"""
import urllib.request
import json
import sys

URL = "http://127.0.0.1:9090/api/mensaje"
PAYLOAD = {"objetivo": "saluda y dime qué puedes hacer", "user": "max"}

print("Enviando POST...", flush=True)
try:
    data = json.dumps(PAYLOAD).encode()
    req = urllib.request.Request(URL, data=data,
                                  headers={"Content-Type": "application/json"})
    r = urllib.request.urlopen(req, timeout=60)
    out = r.read().decode()
    with open("/tmp/test_post_out.txt", "w") as f:
        f.write(out)
    print(f"OK len={len(out)}", flush=True)
    print(out[:2000], flush=True)
except Exception as e:
    with open("/tmp/test_post_err.txt", "w") as f:
        f.write(str(e))
    print(f"ERROR: {e}", flush=True)
