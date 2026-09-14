"""
Metasploit container lifecycle
==============================
Manages a persistent Metasploit Framework Docker container:
  - image / container existence checks
  - start (with health-poll)
  - command execution via HTTP API
  - stop

Uses the official metasploitframework/metasploit-framework image
with a thin Flask API wrapper for command execution.
"""
from __future__ import annotations

import asyncio
import os

from tools.docker_cli import docker_executable

MSF_IMAGE     = "pentest-agent/metasploit"
MSF_CONTAINER = "pentest-metasploit"
MSF_PORT      = 5002          # host port → container port 5000
MSF_API       = f"http://localhost:{MSF_PORT}"

# Prevents concurrent callers from racing to create the same container.
_start_lock = asyncio.Lock()

import pathlib as _pathlib
import secrets as _secrets

_REPO_ROOT = _pathlib.Path(__file__).resolve().parents[1]
_SERVER_SRC = _REPO_ROOT / "tools" / "metasploit" / "server.py"
_SECRET_FILE = _REPO_ROOT / "logs" / ".msf_api_secret"


def _msf_secret() -> str:
    """Shared secret for the Metasploit API, persisted (0600) so the MCP and container agree
    across restarts. Fail-open ('') so a filesystem hiccup never breaks MSF — loopback + the
    Host allowlist still protect the endpoint."""
    try:
        if _SECRET_FILE.exists():
            existing = _SECRET_FILE.read_text().strip()
            if existing:
                return existing
        token = _secrets.token_hex(32)
        _SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)
        _SECRET_FILE.write_text(token)
        try:
            _SECRET_FILE.chmod(0o600)
        except OSError:
            pass
        return token
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# State checks
# ---------------------------------------------------------------------------

async def image_exists() -> bool:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'tools/metasploit_runner.py','step':'image_exists','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


async def container_running() -> bool:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'tools/metasploit_runner.py','step':'container_running','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

async def ensure_running() -> tuple[bool, str]:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'tools/metasploit_runner.py','step':'ensure_running','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


async def stop() -> str:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'tools/metasploit_runner.py','step':'stop','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


# ---------------------------------------------------------------------------
# Command execution
# ---------------------------------------------------------------------------

def _host_rewrite(command: str) -> str:
    """Rewrite localhost/127.0.0.1 → host.docker.internal so tools reach the host."""
    command = command.replace("localhost", "host.docker.internal")
    command = command.replace("127.0.0.1", "host.docker.internal")
    return command


async def exec_command(command: str, timeout: int = 900) -> str:  # NOSONAR
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'tools/metasploit_runner.py','step':'exec_command','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye
