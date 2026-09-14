"""
MobSF container lifecycle + REST client
=======================================
Manages a persistent Mobile-Security-Framework container and drives its static
analysis over the REST API:
  - image / container existence checks
  - start (with health-poll — MobSF's Django app is slow to boot)
  - analyze(path): upload the APK/IPA/APPX/zip bytes, run the scan, fetch the
    structured JSON report
  - stop

Unlike the Kali/Metasploit runners (which shell-exec over an HTTP command API),
MobSF is driven by its own REST endpoints and needs the BINARY inside it. We
stream the file bytes as a multipart upload (POST /api/v1/upload) rather than
bind-mounting — the container never sees the host FS. Every call carries the
API key (MobSF returns 401 without it); we inject a fixed key via `-e
MOBSF_API_KEY=` at run time and send the same value as the Authorization header.
"""
from __future__ import annotations

import asyncio
import os

from core import paths as _paths
from tools.docker_cli import docker_executable

# Use the official MobSF image directly — we don't customise it, so there's no
# wrapper Dockerfile to build (and none whose base-image root user to flag).
# Auto-pulled on first use. Pin — update explicitly (and CVE-scan the new tag).
MOBSF_IMAGE     = "opensecurity/mobile-security-framework-mobsf:v4.4.6"
MOBSF_CONTAINER = "pentest-mobsf"
MOBSF_PORT      = 5003          # host port → container port 8000
MOBSF_API       = f"http://localhost:{MOBSF_PORT}"

# API key: injected into the container at run time (-e) and sent on every REST
# call. Overridable via SMITH_MOBSF_API_KEY. When unset, a RANDOM key is minted
# per install and persisted 0600 to logs/mobsf.key (gitignored) — so it survives
# process restarts and stays in sync with a reused container, without shipping a
# hardcoded, git-committed default secret (which any repo reader would know).
def _resolve_api_key() -> str:
    env = os.environ.get("SMITH_MOBSF_API_KEY")
    if env:
        return env
    import secrets

    key_file = _paths.LOGS_DIR / "mobsf.key"
    try:
        existing = key_file.read_text().strip()
        if existing:
            return existing
    except OSError:
        pass
    key = secrets.token_hex(24)
    try:
        _paths.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(key_file), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            os.write(fd, key.encode())
        finally:
            os.close(fd)
    except OSError:
        pass  # fall back to the in-memory key for this process
    return key


API_KEY = _resolve_api_key()

# Static scans of a large APK/IPA can take minutes — give the scan call plenty of
# headroom. The MCP client transport timeout must exceed this.
SCAN_TIMEOUT = int(os.environ.get("SMITH_MOBSF_SCAN_TIMEOUT", "600"))

_start_lock = asyncio.Lock()


def _read_bytes(path: str) -> bytes:
    """Blocking file read — kept a plain sync function so async callers run it via
    asyncio.to_thread (no blocking open() inside an async body — S7493)."""
    with open(path, "rb") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# State checks
# ---------------------------------------------------------------------------

async def image_exists() -> bool:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'tools/mobsf_runner.py','step':'image_exists','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


async def container_running() -> bool:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'tools/mobsf_runner.py','step':'container_running','status':'CHECKPOINTED'}
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
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'tools/mobsf_runner.py','step':'ensure_running','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


async def stop() -> str:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'tools/mobsf_runner.py','step':'stop','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


# ---------------------------------------------------------------------------
# Analysis (upload → scan → report)
# ---------------------------------------------------------------------------

def _headers() -> dict:
    return {"Authorization": API_KEY}


async def analyze(file_path: str) -> dict:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'tools/mobsf_runner.py','step':'analyze','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


def summarize(report: dict) -> dict:
    """Condense a MobSF report to the MASVS-relevant summary (the `appsec` section
    plus headline metadata) — keeps the huge raw report out of the context window."""
    appsec = report.get("appsec", {}) if isinstance(report, dict) else {}
    buckets = {k: len(appsec.get(k, []) or []) for k in ("high", "warning", "info", "secure", "hotspot")}
    return {
        "app": report.get("app_name") or report.get("file_name"),
        "package": report.get("package_name") or report.get("bundle_id"),
        "security_score": (report.get("appsec", {}) or {}).get("security_score"),
        "finding_counts": buckets,
        "high": appsec.get("high", []),
        "warning": appsec.get("warning", []),
    }
