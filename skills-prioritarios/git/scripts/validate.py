#!/usr/bin/env python3
"""validate.py — git"""
import json, subprocess, os, sys, tempfile

with tempfile.TemporaryDirectory() as d:
    os.chdir(d)
    subprocess.run(["git","init","-q"], check=True)
    subprocess.run(["git","config","user.email","Mavis@MiniMax"], check=True)
    subprocess.run(["git","config","user.name","Mavis"], check=True)
    with open("a.txt","w") as f: f.write("hello")
    p = subprocess.run(
        ["python3", os.path.join(os.path.dirname(__file__), "run.py")],
        input=json.dumps({"action":"status","repo":d}),
        capture_output=True, text=True,
    )
    out = json.loads(p.stdout)
    assert out["ok"] is True, f"status no ok: {out}"
    assert "a.txt" in out["stdout"], f"a.txt no aparece en status: {out}"
    print("  ok status detecta archivos sin commit")
print("PASS git")
