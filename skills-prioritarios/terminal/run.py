#!/usr/bin/env python3
"""run.py — terminal (bash sandboxed wrapper)"""
import json, sys, os, subprocess, re, time

BLACKLIST = [
    r"rm\s+-rf\s+/($|\s)",
    r"rm\s+-rf\s+--no-preserve-root",
    r"chmod\s+-R\s+777\s+/",
    r"mkfs",
    r"dd\s+if=",
    r":\(\)\s*\{",
    r"\bshutdown\b",
    r"\breboot\b",
    r"iptables\s+-F",
    r"curl\s+[^|]*\|\s*bash",
]

def is_blocked(cmd):
    for pat in BLACKLIST:
        if re.search(pat, cmd):
            return pat
    return None

def main():
    p = json.loads(sys.stdin.read() or "{}")
    cmd = p["cmd"]
    cwd = p.get("cwd", ".")
    timeout = p.get("timeout_s", 30)
    max_out = p.get("max_output_bytes", 1024 * 1024)

    blocked = is_blocked(cmd)
    if blocked:
        print(json.dumps({"ok": False, "blocked_reason": f"matched: {blocked}"}))
        sys.exit(1)

    env = os.environ.copy()
    env.update(p.get("env") or {})
    t0 = time.time()
    try:
        r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        print(json.dumps({"ok": False, "error": "timeout"})); sys.exit(1)
    dur = time.time() - t0
    out = {
        "ok": r.returncode == 0,
        "returncode": r.returncode,
        "stdout": r.stdout[:max_out],
        "stderr": r.stderr[:max_out],
        "duration_s": round(dur, 3),
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
