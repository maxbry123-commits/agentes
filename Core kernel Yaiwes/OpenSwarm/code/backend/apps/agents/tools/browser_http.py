"""One browser-shaped HTTP request, shared by every keyless web rung.

Search frontends gate on the TLS/JA3 fingerprint of the CLIENT, not on the
headers or the verb. Measured over 8 interleaved randomised rounds against
DuckDuckGo from one machine: plain httpx POST to the html endpoint 4/8, plain
httpx GET to the lite endpoint 4/8 (so switching verb or endpoint changes
nothing), and curl_cffi's Chrome impersonation 8/8 with the same headers, verb
and URL. That is the whole difference between "search sometimes works" and
"search works", so we impersonate whenever curl_cffi imports.

If it doesn't import (a packaging regression), we degrade to httpx with a full
Chrome header set rather than failing: half a search beats no search.

This does NOT validate the target host, so it is only for the FIXED hosts we
choose ourselves. User- or model-supplied URLs must go through
`ssrf_guard.safe_fetch`, which re-checks every redirect hop.
"""

from typing import Dict, Optional

import httpx
from pydantic import BaseModel, ConfigDict
from typeguard import typechecked

CHROME_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# A real navigation sends all of these; httpx sends almost none of them by default.
BROWSER_HEADERS: Dict[str, str] = {
    "User-Agent": CHROME_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

P_IMPERSONATE_PROFILE = "chrome"


class HttpReply(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    status: int
    text: str
    content: bytes
    content_type: str
    url: str


@typechecked
def impersonation_available() -> bool:
    """Whether the TLS-impersonating client is installed in this environment."""
    try:
        import curl_cffi.requests  # noqa: F401
    except Exception:
        return False
    return True


@typechecked
async def p_impersonated(
    url: str, method: str, params: Optional[Dict], headers: Dict[str, str],
    timeout: float, follow_redirects: bool,
) -> HttpReply:
    from curl_cffi.requests import AsyncSession
    async with AsyncSession() as session:
        resp = await session.request(
            method, url, params=params, headers=headers, timeout=timeout,
            impersonate=P_IMPERSONATE_PROFILE, allow_redirects=follow_redirects,
        )
        return HttpReply(
            status=resp.status_code, text=resp.text, content=resp.content,
            content_type=resp.headers.get("content-type", ""), url=str(resp.url),
        )


@typechecked
async def p_plain(
    url: str, method: str, params: Optional[Dict], headers: Dict[str, str],
    timeout: float, follow_redirects: bool,
) -> HttpReply:
    async with httpx.AsyncClient(
        timeout=timeout, follow_redirects=follow_redirects, headers=headers,
    ) as client:
        resp = await client.request(method, url, params=params)
        return HttpReply(
            status=resp.status_code, text=resp.text, content=resp.content,
            content_type=resp.headers.get("content-type", ""), url=str(resp.url),
        )


@typechecked
async def browser_request(
    url: str,
    *,
    method: str = "GET",
    params: Optional[Dict] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 10.0,
    follow_redirects: bool = True,
) -> HttpReply:
    """Fetch `url` looking like Chrome. Fixed hosts only; see the module docstring."""
    merged = dict(BROWSER_HEADERS)
    if headers:
        merged.update(headers)
    if impersonation_available():
        return await p_impersonated(url, method, params, merged, timeout, follow_redirects)
    return await p_plain(url, method, params, merged, timeout, follow_redirects)
