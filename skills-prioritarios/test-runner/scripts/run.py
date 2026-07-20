#!/usr/bin/env python3
"""run.py — test-runner"""
import json, sys, os, subprocess, time

def detect(path):
    if os.path.exists(os.path.join(path, "pyproject.toml")) or os.path.exists(os.path.join(path, "pytest.ini")):
        return "pytest"
    if os.path.exists(os.path.join(path, "package.json")):
        try:
            with open(os.path.join(path, "package.json")) as f:
                pkg = json.load(f)
            if "vitest" in (pkg.get("devDependencies") or {}) or "vitest" in (pkg.get("dependencies") or {}):
                return "vitest"
            if "jest" in (pkg.get("devDependencies") or {}) or "jest" in (pkg.get("dependencies") or {}):
                return "jest"
        except Exception:
            pass
    if os.path.exists(os.path.join(path, "go.mod")): return "go"
    if os.path.exists(os.path.join(path, "Cargo.toml")): return "cargo"
    return "unknown"

def main():
    p = json.loads(sys.stdin.read() or "{}")
    path = p.get("path", ".")
    framework = p.get("framework", "auto")
    max_dur = p.get("max_duration_s", 120)
    if framework == "auto": framework = detect(path)
    cmd_map = {
        "pytest": ["python3","-m","pytest","-q","--tb=line","--no-header"],
        "vitest": ["npx","vitest","run","--reporter=json"],
        "jest":   ["npx","jest","--json"],
        "go":     ["go","test","-json","./..."],
        "cargo":  ["cargo","test","--message-format=json"],
    }
    if framework not in cmd_map:
        print(json.dumps({"ok": False, "error": f"unsupported framework: {framework}"}))
        sys.exit(1)
    t0 = time.time()
    try:
        r = subprocess.run(cmd_map[framework], cwd=path, capture_output=True, text=True, timeout=max_dur)
    except subprocess.TimeoutExpired:
        print(json.dumps({"ok": False, "framework": framework, "error": "timeout"})); sys.exit(1)
    dur = time.time() - t0
    print(json.dumps({
        "ok": r.returncode == 0,
        "framework": framework,
        "duration_s": round(dur, 2),
        "returncode": r.returncode,
        "stdout_tail": r.stdout[-2000:],
        "stderr_tail": r.stderr[-2000:],
    }))

if __name__ == "__main__":
    main()
