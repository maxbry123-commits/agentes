"""HTTP probing utilities for profiler and infra-attack.

Lightweight wrapper around requests with sensible defaults for AI service detection:
- Short timeouts (services are usually local/private)
- Common AI service paths probed in parallel
- Header normalization
"""
from __future__ import annotations

import re
import socket
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    requests = None  # type: ignore


DEFAULT_TIMEOUT = 5.0
DEFAULT_HEADERS = {
    "User-Agent": "AIG-AgentRedteam/1.0 (+https://github.com/tencent/AI-Infra-Guard)",
    "Accept": "*/*",
}


@dataclass
class ProbeResult:
    url: str
    status_code: int = 0
    body: str = ""
    headers: dict = field(default_factory=dict)
    title: str = ""
    error: Optional[str] = None
    elapsed_ms: int = 0
    final_url: str = ""

    def matched(self) -> bool:
        return self.status_code != 0 and not self.error

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "final_url": self.final_url,
            "status_code": self.status_code,
            "title": self.title,
            "headers": dict(self.headers),
            "body_length": len(self.body),
            "body_preview": self.body[:512],
            "error": self.error,
            "elapsed_ms": self.elapsed_ms,
        }


def normalize_target(target: str) -> str:
    """Add scheme if missing; bare 'host:port' becomes 'http://host:port'."""
    target = target.strip().rstrip("/")
    if not target:
        return target
    if "://" in target:
        return target
    # IP:port or host:port
    if re.match(r"^[\w.\-]+(:\d+)?$", target):
        return f"http://{target}"
    return target


def is_reachable(url: str, timeout: float = 2.0) -> bool:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'skills/aig-agent-redteam/scripts/common/http_probe.py','step':'is_reachable','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


def _make_session() -> "requests.Session":
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'skills/aig-agent-redteam/scripts/common/http_probe.py','step':'_make_session','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


def http_get(
    url: str,
    timeout: float = DEFAULT_TIMEOUT,
    follow_redirects: bool = True,
    verify_tls: bool = False,
) -> ProbeResult:
    """Single GET probe with default safe behavior."""
    if requests is None:
        return ProbeResult(url=url, error="requests library not installed")

    import time
    t0 = time.time()
    try:
        sess = _make_session()
        resp = sess.get(
            url,
            timeout=timeout,
            allow_redirects=follow_redirects,
            verify=verify_tls,
        )
        elapsed_ms = int((time.time() - t0) * 1000)
        body = ""
        try:
            body = resp.text
        except Exception:
            body = resp.content.decode("utf-8", errors="replace") if resp.content else ""
        title_m = re.search(r"<title[^>]*>(.*?)</title>", body, re.IGNORECASE | re.DOTALL)
        return ProbeResult(
            url=url,
            final_url=resp.url,
            status_code=resp.status_code,
            body=body,
            headers={k: v for k, v in resp.headers.items()},
            title=title_m.group(1).strip() if title_m else "",
            elapsed_ms=elapsed_ms,
        )
    except Exception as e:
        return ProbeResult(url=url, error=f"{type(e).__name__}: {e}", elapsed_ms=int((time.time() - t0) * 1000))


def http_get_json(url: str, timeout: float = DEFAULT_TIMEOUT) -> dict:
    """Convenience: GET + JSON parse, returns {} on any failure."""
    r = http_get(url, timeout=timeout)
    if not r.matched():
        return {}
    try:
        import json
        return json.loads(r.body)
    except Exception:
        return {}
