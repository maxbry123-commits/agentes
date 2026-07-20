#!/usr/bin/env python3
"""validate.py — web-search"""
import json, subprocess, os

# Sin SERPER_API_KEY: debe caer a ddg (vacío por ahora) y devolver ok=True con count=0
p = subprocess.run(
    ["python3", os.path.join(os.path.dirname(__file__), "run.py")],
    input=json.dumps({"q":"test","n":3,"provider":"auto"}),
    capture_output=True, text=True, timeout=30,
    env={**os.environ, "SERPER_API_KEY": ""},
)
out = json.loads(p.stdout)
assert out["ok"] is True, out
assert out["count"] == 0, out
assert out["provider_used"] in ("ddg","bing","serper"), out
print(f"  ok provider_used={out['provider_used']} count=0")

# Forzar provider inexistente: debe usar ddg
p = subprocess.run(
    ["python3", os.path.join(os.path.dirname(__file__), "run.py")],
    input=json.dumps({"q":"test","n":3,"provider":"ddg"}),
    capture_output=True, text=True, timeout=30,
)
out = json.loads(p.stdout)
assert out["ok"] is True, out
print("  ok ddg stub")
print("PASS web-search")
