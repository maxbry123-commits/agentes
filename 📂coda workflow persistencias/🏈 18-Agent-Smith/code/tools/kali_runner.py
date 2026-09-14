"""
Kali container lifecycle
========================
Manages the persistent kali-mcp Docker container:
  - image / container existence checks
  - start (with health-poll)
  - command execution via the official kali-server-mcp HTTP API
  - stop

Used exclusively by mcp_server.py; not a Tool registry entry.
"""
from __future__ import annotations

import asyncio
import os
import shlex

from tools.docker_cli import docker_executable

KALI_IMAGE     = "pentest-agent/kali-mcp"
KALI_CONTAINER = "pentest-kali"
KALI_PORT      = 5001          # host port → container port 5000
KALI_API       = f"http://localhost:{KALI_PORT}"

# Prevents concurrent callers from racing to create the same container.
_start_lock = asyncio.Lock()

import pathlib as _pathlib
import secrets as _secrets

_REPO_ROOT = _pathlib.Path(__file__).resolve().parents[1]
_GUARD_SRC = _REPO_ROOT / "tools" / "kali" / "api_guard.py"
_TOKEN_FILE = _REPO_ROOT / "logs" / ".kali_api_token"
# kali-server-mcp runs loopback-only inside the container on this port; only the
# in-container guard (published on :5000) can reach it.
_KALI_UPSTREAM_PORT = "5555"


def _kali_token() -> str:
    """Shared secret between the MCP and the in-container API guard, persisted (0600) so
    both agree across restarts. Fail-open ('') so a filesystem hiccup never breaks Kali —
    the guard then runs open and logs a warning."""
    try:
        if _TOKEN_FILE.exists():
            existing = _TOKEN_FILE.read_text().strip()
            if existing:
                return existing
        token = _secrets.token_hex(32)
        _TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        _TOKEN_FILE.write_text(token)
        try:
            _TOKEN_FILE.chmod(0o600)
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
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'tools/kali_runner.py','step':'image_exists','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


async def container_running() -> bool:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'tools/kali_runner.py','step':'container_running','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

def _forward_ai_keys(environ) -> list[str]:
    """docker ``-e`` flags for the AI API keys forwarded into the Kali container. AITEST_ANTHROPIC_API_KEY
    (kept out of Claude Code's ANTHROPIC_API_KEY so it can't bill the Smith agent) is forwarded AS
    ANTHROPIC_API_KEY for the in-container tools; a bare ANTHROPIC_API_KEY (SMITH_USE_API_KEY=yes / legacy)
    overrides it when both are set."""
    fwd: dict[str, str] = {}
    for src, dst in (("OPENAI_API_KEY", "OPENAI_API_KEY"),
                     ("AITEST_ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY"),
                     ("ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY"),
                     ("AZURE_OPENAI_API_KEY", "AZURE_OPENAI_API_KEY")):
        if environ.get(src):
            fwd[dst] = environ[src]
    return [x for dst, val in fwd.items() for x in ("-e", f"{dst}={val}")]


async def ensure_running() -> tuple[bool, str]:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'tools/kali_runner.py','step':'ensure_running','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


async def _seed_curl_defaults() -> None:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'tools/kali_runner.py','step':'_seed_curl_defaults','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


async def stop() -> str:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'tools/kali_runner.py','step':'stop','status':'CHECKPOINTED'}
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


def _force_bash(command: str) -> str:
    """Wrap the command in `bash -c` so bash-only syntax works.

    kali-server-mcp executes commands via /bin/sh, which on Kali/Debian is
    dash — it does NOT support `[[ ]]`, arrays, `<(...)`, brace expansion,
    `==` in test, and other bashisms. Agents routinely produce bash-shaped
    one-liners, and without this wrapper every such command hits
    `[[: not found` and silently returns a partial or empty result.

    The command is quoted with `shlex.quote` so inner quotes, `$`, and
    backslashes survive intact. Already-wrapped commands (`bash -c '...'`)
    end up double-wrapped, which is harmless: the outer bash invokes the
    inner bash.
    """
    if not command.strip():
        return command
    return f"bash -c {shlex.quote(command)}"


async def exec_command(command: str, timeout: int = 600) -> str:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'tools/kali_runner.py','step':'exec_command','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye
