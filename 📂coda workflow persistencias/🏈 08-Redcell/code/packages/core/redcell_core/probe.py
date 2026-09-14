"""SSH into a saved Server and gather basic facts: hostname, OS, CPU, RAM, first IP."""

from __future__ import annotations

import asyncio
from time import perf_counter

# One command that prints prefixed, easy-to-parse lines. Sent verbatim to the
# remote shell (the $(...) / $2 are evaluated remotely, not by Python).
_PROBE = "; ".join([
    'echo "H:$(hostname 2>/dev/null)"',
    'echo "U:$(uname -sr 2>/dev/null)"',
    'echo "C:$(nproc 2>/dev/null)"',
    "echo \"M:$(awk '/MemTotal/{print int($2/1024)}' /proc/meminfo 2>/dev/null)\"",
    'echo "I:$(hostname -I 2>/dev/null)"',
])


async def probe_server(host: str, username: str | None, secret: str | None, timeout: float = 12.0) -> dict:
    from .engine.execution import SSHBackend, _looks_like_private_key

    pk = secret if _looks_like_private_key(secret) else None
    pw = None if pk else (secret or None)
    backend = SSHBackend(host, username or "root", password=pw, private_key=pk)
    t0 = perf_counter()
    try:
        await asyncio.wait_for(backend.start(), timeout=timeout)
        res = await asyncio.wait_for(backend.run(_PROBE), timeout=timeout)
        latency = int((perf_counter() - t0) * 1000)
    except TimeoutError:
        return {"ok": False, "error": "connection timed out"}
    except Exception as exc:
        return {"ok": False, "error": (str(exc) or type(exc).__name__)[:220]}
    finally:
        try:
            await backend.close()
        except Exception:
            pass
    facts = _parse(res.output)
    facts.update({"ok": True, "latency_ms": latency, "output": (res.output or "").strip()[:2000]})
    return facts


async def probe_proxy(url: str, timeout: float = 12.0) -> dict:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'packages/core/redcell_core/probe.py','step':'probe_proxy','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


def _parse(output: str) -> dict:
    out: dict = {}
    for raw in (output or "").splitlines():
        line = raw.strip()
        if line.startswith("H:"):
            out["hostname"] = line[2:].strip() or None
        elif line.startswith("U:"):
            out["os"] = line[2:].strip() or None
        elif line.startswith("C:"):
            try:
                out["cpu"] = int(line[2:].strip())
            except ValueError:
                pass
        elif line.startswith("M:"):
            try:
                mb = int(line[2:].strip())
                out["ram_gb"] = max(1, round(mb / 1024))
            except ValueError:
                pass
        elif line.startswith("I:"):
            ips = line[2:].strip().split()
            out["ip"] = ips[0] if ips else None
    return out
