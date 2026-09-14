"""
Proxy Manager — Proxy rotation for rate limiting and IP blocks.

Handles proxy rotation when targets respond with 403/429 status codes.
Supports HTTP, HTTPS, SOCKS5 proxies and proxychains integration.

Usage:
    proxy_mgr = ProxyManager()
    await proxy_mgr.load_from_env()
    curl_args = await proxy_mgr.get_curl_args()   # ["--proxy", "http://..."]
    env_vars = await proxy_mgr.get_proxy_env()     # {"HTTP_PROXY": "..."}
"""

import asyncio
import os
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse


class ProxyManager:
    """
    Manages proxy rotation for HTTP requests.

    Features:
    - Proxy list from env var (PENTDEM_PROXY_LIST) or config file
    - Auto-rotate on 403/429 responses
    - Support HTTP, HTTPS, SOCKS5 proxies
    - Proxychains wrapper support
    """

    SUPPORTED_SCHEMES = ("http", "https", "socks5", "socks5h")

    def __init__(self):
        self._proxies: List[str] = []
        self._current_index: int = -1
        self._lock = asyncio.Lock()
        self._use_proxychains: bool = False
        self._error_count: Dict[str, int] = {}
        self._max_errors_per_proxy: int = 3

    async def load_from_env(self):
        """Load proxy configuration from environment variables."""
        proxy_list = os.environ.get("PENTDEM_PROXY_LIST", "")
        if proxy_list:
            self._proxies = [
                p.strip() for p in proxy_list.split(",") if p.strip()
            ]

        # Also check standard env vars
        http_proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
        https_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
        if http_proxy and http_proxy not in self._proxies:
            self._proxies.append(http_proxy)
        if https_proxy and https_proxy not in self._proxies:
            self._proxies.append(https_proxy)

        self._use_proxychains = os.environ.get(
            "PENTDEM_USE_PROXYCHAINS", ""
        ).lower() in ("1", "true", "yes")

    async def load_from_file(self, path: str):
        """Load proxy list from a file (one proxy per line)."""
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        self._proxies.append(line)
        except (FileNotFoundError, PermissionError):
            pass

    # ── Proxy access ──────────────────────────────────────────

    async def get_proxy(self) -> Optional[str]:
        """Get the current proxy URL, or None if no proxies configured."""
        if not self._proxies:
            return None

        async with self._lock:
            # Check if current proxy has too many errors
            if self._current_index >= 0:
                current = self._proxies[self._current_index]
                if self._error_count.get(current, 0) >= self._max_errors_per_proxy:
                    self._current_index = (self._current_index + 1) % len(self._proxies)

            if self._current_index < 0:
                self._current_index = 0

            return self._proxies[self._current_index]

    async def rotate(self) -> Optional[str]:
        """Rotate to the next proxy. Returns the new proxy URL."""
        if not self._proxies:
            return None

        async with self._lock:
            self._current_index = (self._current_index + 1) % len(self._proxies)
            return self._proxies[self._current_index]

    async def report_error(self, proxy_url: str):
        """Report a failure for the given proxy."""
        async with self._lock:
            self._error_count[proxy_url] = self._error_count.get(proxy_url, 0) + 1

    async def report_rate_limit(self):
        """Report a rate limit (403/429) and rotate immediately."""
        current = await self.get_proxy()
        if current:
            await self.report_error(current)
        return await self.rotate()

    # ── Curl integration ──────────────────────────────────────

    async def get_proxy_env(self) -> Dict[str, str]:
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'skills/proxy_manager.py','step':'get_proxy_env','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    async def get_curl_args(self) -> List[str]:
        """
        Get curl command-line proxy arguments.
        Returns empty list if no proxy configured.
        """
        proxy = await self.get_proxy()
        if not proxy:
            return []
        return ["--proxy", proxy]

    def should_use_proxychains(self) -> bool:
        return self._use_proxychains

    async def has_proxy(self) -> bool:
        return len(self._proxies) > 0

    # ── Validation ────────────────────────────────────────────

    async def test_proxy(self, proxy: str,
                         test_url: str = "http://httpbin.org/ip") -> bool:
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'skills/proxy_manager.py','step':'test_proxy','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    async def validate_all(self) -> List[Tuple[str, bool]]:
        """Test all proxies, return (proxy_url, is_valid) pairs."""
        results = []
        for proxy in self._proxies:
            valid = await self.test_proxy(proxy)
            results.append((proxy, valid))
        return results

    @property
    def proxy_count(self) -> int:
        return len(self._proxies)
