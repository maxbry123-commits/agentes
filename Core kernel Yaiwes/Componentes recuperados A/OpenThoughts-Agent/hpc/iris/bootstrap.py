"""Command wrapping for Iris task entrypoints."""

from __future__ import annotations

import os
import shlex


def wrap_task_command(
    command: list[str],
    *,
    extras: list[str],
    needs_tpu_runtime_patch: bool,
) -> list[str]:
    """Wrap Python entrypoints with the OT-Agent Iris runtime bootstrap."""
    if not (command and command[0] == "python" and len(command) >= 2):
        return command

    is_module = command[1] == "-m"
    if is_module and len(command) < 3:
        raise ValueError("python -m requires a module name")
    target = command[2] if is_module else command[1]
    target_argv = command[3:] if is_module else command[2:]
    run_target = (
        "runpy.run_module(sys.argv[0], run_name='__main__', alter_sys=True)"
        if is_module
        else "runpy.run_path(sys.argv[0], run_name='__main__')"
    )
    py_bootstrap = (
        "import sys; "
        "sys.path.append('/app'); "
        "sys.argv = sys.argv[1:]; "
        "import runpy; "
        f"{run_target}"
    )
    extras_flags = " ".join(
        f"--extra {shlex.quote(e.split(':', 1)[-1])}" for e in extras
    )
    quiet = "" if os.environ.get("IRIS_DEBUG_UV_RESYNC") else "--quiet"
    resync_cmd = (
        "cd /app && "
        f"uv sync {quiet} --frozen --reinstall --link-mode=copy "
        f"--all-packages --no-group dev {extras_flags}".rstrip()
    )
    patch_cmd = (
        "python scripts/iris/patch_tpu_inference.py"
        if needs_tpu_runtime_patch
        else "true"
    )
    py_invoke = shlex.join(["python", "-c", py_bootstrap, target, *target_argv])
    bash_cmd = (
        f"set -e; {resync_cmd}; "
        "export PATH=/app/.venv/bin:$PATH; "
        f"{patch_cmd}; exec {py_invoke}"
    )
    return ["bash", "-c", bash_cmd]
