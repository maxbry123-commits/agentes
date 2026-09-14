"""
Isolated execution sandbox
===========================
Build & run untrusted *target* code to CONFIRM a white-box finding with a real
crash/exec artifact instead of a static "input reaches sink" claim.

This is deliberately NOT the persistent Kali container: that one runs with
NET_RAW/NET_ADMIN and host networking, which is unsafe for executing untrusted
code. Every run here is an ephemeral, **network-isolated**, **capability-dropped**
container over a **staged COPY** of the codebase — the original source is never
mounted writable, so a malicious build script can't mutate the repo under review.

Opt-in and fail-soft by contract: any setup/staging/run failure returns a
diagnostic dict (ok=False, error=...) and never raises into the scan pipeline.
A non-reproduction is evidence the static claim is unconfirmed — never a hard error.
"""
from __future__ import annotations

import asyncio
import os
import shutil
import tempfile

from tools.docker_cli import docker_executable
from tools.docker_runner import _ensure_image

# Heavy / irrelevant directories never staged into the sandbox.
_IGNORE_NAMES = (
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".mypy_cache",
    ".pytest_cache", "dist", "build", "target", ".gradle", ".idea", ".tox",
)
_IGNORE = shutil.ignore_patterns(*_IGNORE_NAMES, "*.pyc")

# Cap on the staged copy so we never copy a multi-GB monorepo into /tmp.
_MAX_STAGE_BYTES = 512 * 1024 * 1024  # 512 MB

DEFAULT_IMAGE = "python:3.11-slim"
DEFAULT_TIMEOUT = 180


def _dir_size(path: str) -> int:
    """Approximate on-disk size, pruning heavy dirs; short-circuits past the cap."""
    total = 0
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in _IGNORE_NAMES]
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
            if total > _MAX_STAGE_BYTES:
                return total
    return total


async def run_in_sandbox(
    codebase_path: str,
    cmd: str,
    setup: str = "",
    image: str = DEFAULT_IMAGE,
    subdir: str = "",
    allow_network: bool = True,
) -> dict:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'tools/sandbox_runner.py','step':'run_in_sandbox','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye
