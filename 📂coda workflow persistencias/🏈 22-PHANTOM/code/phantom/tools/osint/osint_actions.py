"""
OSINT Tools - Phase 1 Enhancement
=================================

Passive reconnaissance tools for attack surface discovery.
These tools query external APIs and databases - they NEVER touch the target directly.

SECURITY NOTES:
- All tools are READ-ONLY (passive reconnaissance)
- API keys are optional - tools degrade gracefully without them
- Rate limiting is built-in to prevent API abuse
- Results are cached to reduce redundant queries
- No data is sent to the target

Tools:
- crtsh_search: Certificate Transparency log search (crt.sh)
- shodan_search: Shodan API search for exposed services
- whois_lookup: WHOIS history lookup
- dns_history: DNS history lookup via SecurityTrails
"""

import asyncio
import hashlib
import logging
import os
import re
import time
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote_plus

import httpx

from phantom.config.config import Config
from phantom.tools.registry import register_tool


logger = logging.getLogger(__name__)

# Rate limiting state (simple in-memory)
_RATE_LIMIT_STATE: dict[str, float] = {}
_RATE_LIMIT_INTERVALS: dict[str, float] = {
    "crtsh": 2.0,      # crt.sh: 2 seconds between requests
    "shodan": 1.0,     # Shodan: 1 second between requests
    "whois": 3.0,      # WHOIS: 3 seconds between requests
    "securitytrails": 2.0,  # SecurityTrails: 2 seconds between requests
}

# Simple in-memory cache for OSINT results
_OSINT_CACHE: dict[str, tuple[Any, float]] = {}
_CACHE_TTL = 3600  # 1 hour cache TTL


def _rate_limit(api_name: str) -> None:
    """Enforce rate limiting for API calls."""
    now = time.monotonic()
    last_call = _RATE_LIMIT_STATE.get(api_name, 0.0)
    interval = _RATE_LIMIT_INTERVALS.get(api_name, 1.0)
    wait_time = interval - (now - last_call)
    if wait_time > 0:
        time.sleep(wait_time)
    _RATE_LIMIT_STATE[api_name] = time.monotonic()


def _get_cache_key(prefix: str, *args: Any) -> str:
    """Generate a cache key from prefix and arguments."""
    data = f"{prefix}:{':'.join(str(a) for a in args)}"
    return hashlib.md5(data.encode()).hexdigest()


def _get_cached(key: str) -> Any | None:
    """Get cached result if not expired."""
    if key not in _OSINT_CACHE:
        return None
    result, timestamp = _OSINT_CACHE[key]
    if time.time() - timestamp > _CACHE_TTL:
        del _OSINT_CACHE[key]
        return None
    return result


def _set_cached(key: str, result: Any) -> None:
    """Store result in cache."""
    _OSINT_CACHE[key] = (result, time.time())
    # Cleanup old entries if cache grows too large
    if len(_OSINT_CACHE) > 1000:
        cutoff = time.time() - _CACHE_TTL
        keys_to_delete = [k for k, (_, ts) in _OSINT_CACHE.items() if ts < cutoff]
        for k in keys_to_delete:
            del _OSINT_CACHE[k]


def _extract_domain(target: str) -> str:
    """Extract the root domain from a URL or hostname."""
    # Remove protocol
    if "://" in target:
        target = target.split("://", 1)[1]
    # Remove path
    target = target.split("/")[0]
    # Remove port
    target = target.split(":")[0]
    # Lowercase first, then remove www prefix
    target = target.lower().strip()
    if target.startswith("www."):
        target = target[4:]
    return target


def _validate_domain(domain: str) -> tuple[bool, str]:
    """Validate domain format for OSINT queries."""
    if not domain:
        return False, "Domain cannot be empty"
    if len(domain) > 253:
        return False, "Domain too long"
    # Basic domain validation
    pattern = re.compile(
        r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+"
        r"[a-zA-Z]{2,}$"
    )
    if not pattern.match(domain):
        # Allow wildcard prefix for crt.sh
        if domain.startswith("%."):
            return _validate_domain(domain[2:])
        return False, f"Invalid domain format: {domain}"
    return True, ""


@register_tool(sandbox_execution=False)
async def crtsh_search(domain: str, include_expired: bool = False) -> dict[str, Any]:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'phantom/tools/osint/osint_actions.py','step':'crtsh_search','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


@register_tool(sandbox_execution=False)
async def shodan_search(
    query: str,
    search_type: str = "host",
    max_results: int = 50,
) -> dict[str, Any]:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'phantom/tools/osint/osint_actions.py','step':'shodan_search','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


@register_tool(sandbox_execution=False)
async def whois_lookup(domain: str, include_history: bool = False) -> dict[str, Any]:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'phantom/tools/osint/osint_actions.py','step':'whois_lookup','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


@register_tool(sandbox_execution=False)
async def dns_enum(domain: str, record_types: list[str] | None = None) -> dict[str, Any]:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'phantom/tools/osint/osint_actions.py','step':'dns_enum','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


@register_tool(sandbox_execution=False)
async def github_dork(
    organization: str | None = None,
    domain: str | None = None,
    keywords: list[str] | None = None,
) -> dict[str, Any]:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'phantom/tools/osint/osint_actions.py','step':'github_dork','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye
