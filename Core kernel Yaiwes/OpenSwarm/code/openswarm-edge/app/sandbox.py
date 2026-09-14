"""Sandboxed Python runner for published apps' backend.py compute.

VENDORED from backend/apps/outputs/executor.py (the desktop App Builder runtime).
Keep the subprocess hardening in sync with that file; this is the same
data-shaping sandbox, just running in the edge instead of on the desktop. The
static gate it runs on every call lives in the vendored app/code_safety.py. Pure
compute only: no network, no disk, no subprocess, no secrets. Safe to run
multi-tenant on one machine because nothing here can reach shared state."""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
from dataclasses import dataclass

from app.code_safety import ALLOWED_MODULES, validate_code_safety

TIMEOUT_SECONDS = 30


def _minimal_env() -> dict:
    return {
        "PYTHONDONTWRITEBYTECODE": "1",
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
    }


@dataclass
class ComputeResult:
    result: dict
    stdout: str


async def run_backend(code: str, input_data: dict) -> ComputeResult:
    """Validate + execute user backend code in a hardened subprocess. The code
    reads `input_data` (a global dict) and assigns a global `result` dict."""
    validate_code_safety(code)

    preamble = (
        "import json, sys, io, builtins\n"
        "p_stdout = sys.stdout\n"
        "p_capture = io.StringIO()\n"
        "sys.stdout = p_capture\n"
        "input_data = json.loads(sys.stdin.read())\n"
        "result = {}\n"
        # Warm the allowlist BEFORE scrubbing builtins: half the stdlib borrows the builtins the scrub deletes while it loads (tokenize does `from builtins import open`, taking `import dataclasses` with it). Then the module handles go, because leaving `sys` bound hands gate-passing code a live `sys.modules['os']` with no import statement in sight.
        f"for p_name in {tuple(sorted(ALLOWED_MODULES))!r}:\n"
        "    try: __import__(p_name)\n"
        "    except ImportError: pass\n"
        "for p_name in ('open','input','breakpoint','exit','quit'):\n"
        "    try: delattr(builtins, p_name)\n"
        "    except AttributeError: pass\n"
        "del sys, io, builtins, p_name\n"
    )
    postamble = (
        "\np_stdout.write(json.dumps({\"__stdout__\": p_capture.getvalue(), \"__result__\": result}))\n"
    )
    wrapper = preamble + code + postamble

    with tempfile.TemporaryDirectory(prefix="osw-edge-exec-") as workdir:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-c", wrapper,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=workdir,
            env=_minimal_env(),
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=json.dumps(input_data).encode()),
                timeout=TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise RuntimeError(f"compute timed out after {TIMEOUT_SECONDS}s")

    if proc.returncode != 0:
        raise RuntimeError(f"compute failed: {stderr.decode(errors='replace').strip()[:500]}")
    try:
        parsed = json.loads(stdout.decode())
    except json.JSONDecodeError:
        raise RuntimeError("compute did not return valid JSON")
    return ComputeResult(result=parsed.get("__result__", {}), stdout=parsed.get("__stdout__", ""))
