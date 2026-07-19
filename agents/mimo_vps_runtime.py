 cat /opt/nct/agents/mimo/runtime.py 2>/dev/null
#!/usr/bin/env python3
"""Mimo_Code_VPS runtime v10 - REAL subprocess execution (no LLM hallucination).

Endpoint: POST /chat  body={"prompt": "cmd", "timeout_s": N}
Returns: ok, stdout, stderr, exit_code, duration_ms, timestamp, cwd, command, artifacts
"""
import os
import sys
import json
import time
import uuid
import sqlite3
import threading
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime, timezone
from urllib.parse import urlparse

# === GitHub token loader (added v10.1) ===
import os as _os_gh
_AGENTS_GITHUB_ENV = "/opt/nct/secrets/agents_github.env"
if _os_gh.path.isfile(_AGENTS_GITHUB_ENV):
    try:
        with open(_AGENTS_GITHUB_ENV) as _f:
            for _line in _f:
                _line = _line.strip()
                if not _line or _line.startswith("#") or "=" not in _line: continue
                _k, _v = _line.split("=", 1)
                if _k == "MIMO_CODE_VPS_TOKEN":
                    _os_gh.environ["GITHUB_TOKEN"] = _v.strip()
                    _os_gh.environ["GH_TOKEN"] = _v.strip()
                    _os_gh.environ["MIMO_CODE_VPS_TOKEN"] = _v.strip()
    except Exception as _e:
        print(f"[mimo_vps] failed to load github env: {_e}", flush=True)


# Config
WORKSPACE = "/opt/nct"
GIT_REPO = "/opt/nct/repos/agentes"
DB = "/opt/nct/agents/mimo/memory.db"
PORT = 8082

# Memory
def _db():
    c = sqlite3.connect(DB, timeout=5)
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('''CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY, value TEXT, updated_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY, prompt TEXT, stdout TEXT, stderr TEXT, exit_code INTEGER, duration_ms INTEGER, created_at TEXT)''')
    return c

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    def _send(self, code, obj):
        body = json.dumps(obj, indent=2, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        n = int(self.headers.get("Content-Length", 0))
        if n == 0: return {}
        try: return json.loads(self.rfile.read(n).decode("utf-8"))
        except: return {}

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            try:
                pid = os.getpid()
                c = _db()
                c.close()
                self._send(200, {"ok": True, "agent": "mimo-code", "persistent": True,
                                 "pid": pid, "uptime_s": time.time() - START_T,
                                 "workspace": WORKSPACE, "git_repo": GIT_REPO,
                                 "memory_db": DB,
                                 "method": "REAL_subprocess_v10"})
            except Exception as e:
                self._send(500, {"ok": False, "error": str(e)})
        else:
            self._send(404, {"error": "not_found", "path": path})

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._read_body()
        if path == "/chat":
            prompt = body.get("prompt", "").strip()
            if not prompt:
                self._send(400, {"ok": False, "error": "missing prompt"}); return
            timeout_s = int(body.get("timeout_s", 30))
            cwd = body.get("cwd", WORKSPACE)
            result = self._execute(prompt, cwd, timeout_s)
            try:
                c = _db()
                c.execute('INSERT INTO tasks(prompt, stdout, stderr, exit_code, duration_ms, created_at) VALUES(?,?,?,?,?,?)',
                          (prompt[:500], result.get("stdout","")[:5000], result.get("stderr","")[:2000],
                           result.get("exit_code",-1), result.get("duration_ms",0),
                           datetime.now(timezone.utc).isoformat()))
                c.commit(); c.close()
            except Exception as e:
                result["db_error"] = str(e)
            self._send(200, result)
        else:
            self._send(404, {"error": "not_found", "path": path})

    def _execute(self, prompt: str, cwd: str, timeout_s: int) -> dict:
        prompt_clean = prompt.strip()
        for marker in ("EJECUTA:", "EJECUTAR:", "EXEC:", "RUN:"):
            if prompt_clean.upper().startswith(marker):
                prompt_clean = prompt_clean[len(marker):].strip()
                break
        # Detect command
        is_command = (
            prompt_clean.startswith(("/","~",".")) or
            " " in prompt_clean or
            any(c in prompt_clean for c in ["|",";","&","$",">","<","`"]) or
            any(prompt_clean.startswith(p) for p in (
                "git ", "gh ", "curl ", "wget ", "grep ", "ripgrep ", "rg ", "find ", "cat ", "ls ",
                "echo ", "mkdir ", "touch ", "cd ", "ssh ", "python", "pip ", "apt ",
                "which ", "env ", "ps ", "df ", "du ", "free ", "top ", "uname", "whoami", "date", "id "
            ))
        )
        if not is_command:
            return {
                "ok": False,
                "stdout": "",
                "stderr": f"prompt_is_not_a_command: '{prompt_clean[:100]}'",
                "exit_code": -1,
                "duration_ms": 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cwd": cwd,
                "command": prompt_clean,
                "artifacts": [],
            }
        if not os.path.isdir(cwd):
            cwd = WORKSPACE
        t0 = time.time()
        try:
            proc = subprocess.run(
                ["/bin/bash", "-c", prompt_clean],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                env={**os.environ, "HOME": os.environ.get("HOME", "/root"),
                     "PATH": os.environ.get("PATH", "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"),
                     "GIT_TERMINAL_PROMPT": "0"},
            )
            dt = int((time.time() - t0) * 1000)
            return {
                "ok": proc.returncode == 0,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "exit_code": proc.returncode,
                "duration_ms": dt,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cwd": cwd,
                "command": prompt_clean,
                "artifacts": [],
            }
        except subprocess.TimeoutExpired as e:
            dt = int((time.time() - t0) * 1000)
            return {
                "ok": False,
                "stdout": e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or ""),
                "stderr": f"timeout after {timeout_s}s",
                "exit_code": -9,
                "duration_ms": dt,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cwd": cwd,
                "command": prompt_clean,
                "artifacts": [],
            }
        except Exception as e:
            dt = int((time.time() - t0) * 1000)
            return {
                "ok": False,
                "stdout": "",
                "stderr": f"execution_error: {str(e)[:500]}",
                "exit_code": -1,
                "duration_ms": dt,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cwd": cwd,
                "command": prompt_clean,
                "artifacts": [],
            }

START_T = time.time()

def main():
    _db().close()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"[mimo_vps v10 REAL] starting on port {PORT}, workspace={WORKSPACE}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

if __name__ == "__main__":
    main()
root@vmi3428294:~# echo 