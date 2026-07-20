#!/usr/bin/env python3
"""validate.py — test mínimo de task-manager."""
import json, subprocess, os, sys, tempfile

def run(action, path, **kw):
    payload = {"action": action, **kw}
    p = subprocess.run(
        ["python3", os.path.join(os.path.dirname(__file__), "run.py")],
        input=json.dumps(payload), capture_output=True, text=True,
        env={**os.environ, "TASK_MANAGER_PATH": path},
    )
    return json.loads(p.stdout), p.returncode

def assert_eq(label, got, want):
    assert got == want, f"FAIL {label}: got {got}, want {want}"
    print(f"  ok {label}")

# Una sola path compartida entre todas las llamadas
tmp = tempfile.mktemp(suffix=".json")

# 1. add
out, _ = run("add", tmp, title="demo", owner="M3")
assert_eq("add.ok", out.get("ok"), True)
assert_eq("add.id_present", bool(out["item"]["id"]), True)
tid = out["item"]["id"]

# 2. list
out, _ = run("list", tmp, status="pending")
assert_eq("list.ok", out.get("ok"), True)
assert_eq("list.count>=1", out["count"] >= 1, True)

# 3. done
out, _ = run("done", tmp, id=tid)
assert_eq("done.ok", out.get("ok"), True)

print("PASS task-manager")
