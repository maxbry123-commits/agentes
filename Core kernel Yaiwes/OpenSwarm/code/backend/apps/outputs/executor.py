import asyncio
import json
import logging
import os
import sys
import tempfile
from dataclasses import dataclass

from backend.apps.outputs.code_safety import ALLOWED_MODULES, validate_code_safety

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 30

# Env vars we always scrub from the subprocess, approved or not. These are the keys an attacker would actually want; install token, provider API keys, cloud credentials. Everything else is local-machine convenience.
P_SCRUBBED_ENV_KEYS = frozenset({
    "OPENSWARM_AUTH_TOKEN",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GOOGLE_API_KEY",
    "GEMINI_API_KEY",
    "OPENROUTER_API_KEY",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "STRIPE_API_KEY",
    "STRIPE_SECRET_KEY",
    "GITHUB_TOKEN",
})


def exec_env(approved: bool = False) -> dict:
    """Build the env for the executor subprocess.

    Sandboxed (approved=False): only language essentials. Gate-passing code is
    data-shaping only; `import os` and `open()` are blocked, so the subprocess
    can't read env vars or expand `~` anyway. No PATH, no HOME.

    Approved (approved=True): the user has explicitly okayed unsafe imports via
    the HITL preview. They expect the code to behave like a normal Python
    process; read HOME, find files, etc. Inherit the real env minus credentials,
    so an `open(os.path.expanduser("~/data.csv"))` actually works instead of
    silently misbehaving.

    Both modes scrub P_SCRUBBED_ENV_KEYS so even approved code never sees the
    install token or provider API keys.
    """
    if approved:
        env = {k: v for k, v in os.environ.items() if k not in P_SCRUBBED_ENV_KEYS}
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        # Force UTF-8 even if the parent somehow lacked it (dev mode where Electron didn't inject PYTHONUTF8). Without this, a child reading non-ASCII stdin/files on a cp1252 Windows machine raises UnicodeDecodeError, the "works on my laptop, not theirs" failure.
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        return env

    env = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
        # LANG/LC_ALL are POSIX-only; on Windows the active code page (cp1252) decides default encoding instead. PYTHONUTF8 + PYTHONIOENCODING force UTF-8 for this from-scratch env so json.loads(sys.stdin.read()) of non-ASCII input_data doesn't blow up on stock Windows machines.
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
    }
    if sys.platform == "win32":
        for k in ("SYSTEMROOT", "WINDIR", "TEMP", "TMP", "USERPROFILE"):
            if k in os.environ:
                env[k] = os.environ[k]
    return env


# The subprocess bootstrap: capture stdout, read the input, and hand the code a `result` to fill. Bound objects rather than modules carry the answer back out, so the hardening below can take the modules away.
P_PREAMBLE = (
    "import json, sys, io, builtins\n"
    "p_stdout = sys.stdout\n"
    "p_capture = io.StringIO()\n"
    "sys.stdout = p_capture\n"
    "input_data = json.loads(sys.stdin.read())\n"
    "result = {}\n"
)
# Warm the allowlist BEFORE scrubbing builtins, because half the stdlib borrows the builtins the scrub deletes while it loads (tokenize does `from builtins import open`, which is how `import dataclasses` dies). Warm imports are cache hits, so gate-passing code never touches the loader again. Then the module handles go: leaving `sys` bound handed gate-passing code a live `sys.modules['os']` with no import statement in sight. exec/eval/compile/__import__ stay put whatever we'd like: the import statement, the loader and namedtuple all run on them, and calling them by name is a static-gate warning anyway.
P_SANDBOX_HARDENING = (
    f"for p_name in {tuple(sorted(ALLOWED_MODULES))!r}:\n"
    "    try: __import__(p_name)\n"
    "    except ImportError: pass\n"
    "for p_name in ('open','input','breakpoint','exit','quit'):\n"
    "    try: delattr(builtins, p_name)\n"
    "    except AttributeError: pass\n"
    "del sys, io, builtins, p_name\n"
)
P_POSTAMBLE = (
    "\np_stdout.write(json.dumps({\"__stdout__\": p_capture.getvalue(), \"__result__\": result}))\n"
)


@dataclass
class BackendExecResult:
    result: dict
    stdout: str
    stderr: str


async def execute_backend_code(
    code: str, input_data: dict, *, approved: bool = False
) -> BackendExecResult:
    """Execute user-provided Python code in a subprocess.

    The code receives ``input_data`` as a global dict and must assign its
    result to a global ``result`` dict.  User print() calls are captured
    separately from the result via an in-process StringIO redirect.

    Security boundaries (defense in depth; none alone is sufficient):
      1. The static gate in code_safety.py, on every run that isn't approved.
      2. Subprocess cwd = fresh temp dir (not the OpenSwarm process cwd).
      3. Subprocess env strips PATH, all *TOKEN / *_API_KEY inheritance.
      4. Preamble scrubs the I/O builtins and drops the module handles it
         needed, so gate-passing code starts with no reachable module.
      5. 30s wall-clock timeout, killed on overrun.

    `approved=True` means a user saw the warnings and clicked Run Anyway, and
    it relaxes 1, 3 and 4 together. It is the ONLY thing that relaxes them: a
    caller that has already run the gate itself still gets the sandbox, because
    "we checked" must never be the reason the walls come down.
    """

    if not approved:
        validate_code_safety(code)

    wrapper = P_PREAMBLE + ("" if approved else P_SANDBOX_HARDENING) + code + P_POSTAMBLE

    with tempfile.TemporaryDirectory(prefix="openswarm-exec-") as workdir:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-c", wrapper,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=workdir,
            env=exec_env(approved=approved),
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=json.dumps(input_data).encode()),
                timeout=TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise RuntimeError(f"Backend code execution timed out after {TIMEOUT_SECONDS}s")

    stderr_text = stderr.decode(errors="replace").strip()

    if proc.returncode != 0:
        raise RuntimeError(f"Backend code error (exit {proc.returncode}): {stderr_text}")

    try:
        parsed = json.loads(stdout.decode())
        return BackendExecResult(
            result=parsed.get("__result__", {}),
            stdout=parsed.get("__stdout__", ""),
            stderr=stderr_text,
        )
    except json.JSONDecodeError:
        raw = stdout.decode(errors="replace").strip()
        raise RuntimeError(
            f"Backend code did not produce valid JSON. Raw output: {raw[:500]}"
        )
