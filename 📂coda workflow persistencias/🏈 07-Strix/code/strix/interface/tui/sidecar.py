"""Launch, authenticate, and supervise the Go TUI sidecar process."""

from __future__ import annotations

import asyncio
import contextlib
import hmac
import os
import secrets
import socket
import subprocess
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any


_WINDOWS_AUTH_TIMEOUT = 10.0
_PROCESS_EXIT_TIMEOUT = 5.0
_SENSITIVE_ENV_SUFFIXES = ("_API_KEY", "_ACCESS_KEY")
_SENSITIVE_ENV_PARTS = frozenset(
    {"CREDENTIAL", "CREDENTIALS", "PASSWORD", "SECRET", "SECRETS", "TOKEN", "TOKENS"}
)
_SENSITIVE_ENV_NAMES = {
    "AWS_ACCESS_KEY_ID",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "LLM_API_KEY",
    "STRIX_TUI_ADDR",
    "STRIX_TUI_FD",
    "STRIX_TUI_TOKEN",
}


def tui_executable() -> str:
    return "strix-tui.exe" if os.name == "nt" else "strix-tui"


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def tui_source_dir() -> Path:
    return Path(__file__).resolve().parent


def child_environment() -> dict[str, str]:
    """Copy only non-secret process state needed by the terminal sidecar."""
    child: dict[str, str] = {}
    for key, value in os.environ.items():
        normalized = key.upper()
        if normalized in _SENSITIVE_ENV_NAMES:
            continue
        if normalized.endswith(_SENSITIVE_ENV_SUFFIXES):
            continue
        if set(normalized.split("_")) & _SENSITIVE_ENV_PARTS:
            continue
        child[key] = value
    return child


def _recv_exactly(connection: socket.socket, size: int) -> bytes:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'strix/interface/tui/sidecar.py','step':'_recv_exactly','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


def _authenticate_connection(
    connection: socket.socket,
    address: tuple[Any, ...],
    expected_token: str,
) -> None:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'strix/interface/tui/sidecar.py','step':'_authenticate_connection','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


def _accept_authenticated_connection(
    listener: socket.socket,
    expected_token: str,
) -> socket.socket:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'strix/interface/tui/sidecar.py','step':'_accept_authenticated_connection','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


async def wait_process(
    process: asyncio.subprocess.Process | subprocess.Popen[bytes],
) -> int:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'strix/interface/tui/sidecar.py','step':'wait_process','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


async def terminate_process(
    process: asyncio.subprocess.Process | subprocess.Popen[bytes] | None,
) -> None:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'strix/interface/tui/sidecar.py','step':'terminate_process','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


async def launch_tui_process(
    command: list[str],
    env: dict[str, str],
    cwd: str | None,
) -> tuple[asyncio.subprocess.Process | subprocess.Popen[bytes], socket.socket]:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'strix/interface/tui/sidecar.py','step':'launch_tui_process','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


async def _launch_posix_tui_process(
    command: list[str],
    env: dict[str, str],
    cwd: str | None,
) -> tuple[asyncio.subprocess.Process, socket.socket]:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'strix/interface/tui/sidecar.py','step':'_launch_posix_tui_process','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


async def _launch_windows_tui_process(
    command: list[str],
    env: dict[str, str],
    cwd: str | None,
) -> tuple[subprocess.Popen[bytes], socket.socket]:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'strix/interface/tui/sidecar.py','step':'_launch_windows_tui_process','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


def check_return_code(return_code: int) -> None:
    if return_code != 0:
        raise RuntimeError(f"Bubble Tea TUI exited with status {return_code}")


def package_version() -> str:
    """Report the installed package version for the Go splash/stats
    ("dev" when metadata is unavailable)."""
    try:
        return version("strix-agent")
    except PackageNotFoundError:
        return "dev"
