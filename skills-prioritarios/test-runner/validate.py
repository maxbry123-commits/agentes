#!/usr/bin/env python3
"""validate.py — test-runner"""
import json, subprocess, os, sys, tempfile

# Crea un mini proyecto pytest temporal
with tempfile.TemporaryDirectory() as d:
    with open(os.path.join(d, "pyproject.toml"), "w") as f:
        f.write("[tool.pytest.ini_options]\n")
    with open(os.path.join(d, "test_demo.py"), "w") as f:
        f.write("def test_ok(): assert 1+1 == 2\n")
    p = subprocess.run(
        ["python3", os.path.join(os.path.dirname(__file__), "run.py")],
        input=json.dumps({"path": d, "framework": "auto"}),
        capture_output=True, text=True, timeout=60,
    )
    out = json.loads(p.stdout)
    assert out["framework"] == "pytest", f"framework detect failed: {out}"
    assert out["ok"] is True, f"pytest no pasó: {out}"
    print("  ok framework_detected=pytest")
    print("  ok tests_passed")
print("PASS test-runner")
