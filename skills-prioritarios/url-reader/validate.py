#!/usr/bin/env python3
"""validate.py — url-reader (no testeamos red; solo JSON shape)"""
import json, subprocess, os

# URL inválida: debe devolver ok=False
p = subprocess.run(
    ["python3", os.path.join(os.path.dirname(__file__), "run.py")],
    input=json.dumps({"url":"http://this-host-does-not-exist.invalid","timeout_s":3}),
    capture_output=True, text=True, timeout=15,
)
out = json.loads(p.stdout)
assert out["ok"] is False, out
assert "error" in out, out
print("  ok url invalida devuelve error")
print("PASS url-reader (offline-check only; smoke real en HF Space)")
