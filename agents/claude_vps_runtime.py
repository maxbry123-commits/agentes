 cat /opt/nct/agents/claude/runtime.py 2>/dev/null
#!/usr/bin/env python3
"""Claude_Code_VPS runtime v10 - REAL subprocess execution (no LLM hallucination).

Endpoint: POST /chat  body={"prompt": "cmd", "timeout_s": N}
Returns: ok, stdout, stderr, exit_code, duration_ms, timestamp, cwd, command, artifacts

Authenticates to GitHub via SSH key (gh CLI not required).
Uses git for repo ops, grep for RAG, curl for web.
NEVER calls any LLM. NEVER invents values.
"""
import os
import sys
import json
import time
import uuid
import shutil
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
                if _k == "CLAUDE_CODE_VPS_TOKEN":
                    _os_gh.environ["GITHUB_TOKEN"] = _v.strip()
                    _os_gh.environ["GH_TOKEN"] = _v.strip()
                    _os_gh.environ["CLAUDE_CODE_VPS_TOKEN"] = _v.strip()
    except Exception as _e:
        print(f"[claude_vps] failed to load github env: {_e}", flush=True)


# Config
SANDBOX = "/opt/nct/agents/claude/sandbox/workspace"
os.makedirs(SANDBOX, exist_ok=True)
DB = "/opt/nct/agents/claude/memory.db"
GIT_DIR = "/opt/nct/agents/claude/sandbox/git"
os.makedirs(GIT_DIR, exist_ok=True)
PORT = 8081

# Memory (minimal)
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
                self._send(200, {"ok": True, "agent": "claude-code", "persistent": True,
                                 "sandbox": SANDBOX, "memory": DB, "git": GIT_DIR,
                                 "pid": pid, "uptime_s": time.time() - START_T,
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
            cwd = body.get("cwd", SANDBOX)
            result = self._execute(prompt, cwd, timeout_s)
            # persist
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
        """Real subprocess execution. NO LLM, NO hallucination."""
        # Determine command strategy based on prompt prefix
        prompt_clean = prompt.strip()
        # strip leading "EJECUTA:" or "EXEC:" marker if present
        for marker in ("EJECUTA:", "EJECUTAR:", "EXEC:", "RUN:"):
            if prompt_clean.upper().startswith(marker):
                prompt_clean = prompt_clean[len(marker):].strip()
                break
        # Strategy 1: prompt IS the command (e.g. "ls -la", "gh repo list")
        # Strategy 2: prompt contains "&&" or "|" or ";" or "$" or ">" — treat as shell
        # Strategy 3: single word/phrase — treat as informational, NOT a command
        is_command = (
            prompt_clean.startswith(("/","~",".")) or  # path
            " " in prompt_clean or  # multi-word
            any(c in prompt_clean for c in ["|",";","&","$",">","<","`"]) or
            prompt_clean.startswith("git ") or
            prompt_clean.startswith("gh ") or
            prompt_clean.startswith("curl ") or
            prompt_clean.startswith("wget ") or
            prompt_clean.startswith("grep ") or
            prompt_clean.startswith("ripgrep ") or
            prompt_clean.startswith("rg ") or
            prompt_clean.startswith("find ") or
            prompt_clean.startswith("cat ") or
            prompt_clean.startswith("ls ") or
            prompt_clean.startswith("echo ") or
            prompt_clean.startswith("mkdir ") or
            prompt_clean.startswith("touch ") or
            prompt_clean.startswith("cd ") or
            prompt_clean.startswith("ssh ") or
            prompt_clean.startswith("python") or
            prompt_clean.startswith("pip ") or
            prompt_clean.startswith("apt ") or
            prompt_clean.startswith("which ") or
            prompt_clean.startswith("env ") or
            prompt_clean.startswith("ps ") or
            prompt_clean.startswith("df ") or
            prompt_clean.startswith("du ") or
            prompt_clean.startswith("free ") or
            prompt_clean.startswith("top ") or
            prompt_clean.startswith("uname") or
            prompt_clean.startswith("whoami") or
            prompt_clean.startswith("date") or
            prompt_clean.startswith("id ")
        )
        if not is_command:
            # Not a command — return error (no hallucination)
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
        # Execute via /bin/bash -c
        if not os.path.isdir(cwd):
            cwd = SANDBOX
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
    # Init db
    _db().close()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"[claude_vps v10 REAL] starting on port {PORT}, sandbox={SANDBOX}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

if __name__ == "__main__":
    main()
root@vmi3428294:~# echo 