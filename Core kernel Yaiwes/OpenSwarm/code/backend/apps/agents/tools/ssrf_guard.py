"""SSRF guard for the agent's web fetchers.

Blocks fetches that would target private/internal IPs (RFC1918, link-local
incl. cloud metadata, CGNAT, multicast, ULA v6, etc). Resolution is async
(non-blocking) and covers both IPv4 AND IPv6 via getaddrinfo.

Loopback (127/8, ::1) is INTENTIONALLY allowed because the desktop app's App
Builder previews servers on 127.0.0.1:<random> and the agent needs to be able
to verify the built app actually runs. The user owns the loopback surface on
their own machine; the realistic SSRF threat for a desktop app is cloud
metadata (169.254.169.254) + internal corporate LANs, not localhost.
"""

from __future__ import annotations

import asyncio
import ipaddress
import logging
from urllib.parse import urljoin, urlparse

import httpx

logger = logging.getLogger(__name__)


class SSRFBlocked(Exception):
    """A fetch was refused because it targets a forbidden IP range."""


class DomainUnreachable(SSRFBlocked):
    """The host has no DNS records at all: dead domain, typo, or no network.

    A subclass so every existing `except SSRFBlocked` still fails closed, but
    callers that care can tell "we refused this" apart from "this doesn't
    exist", which are opposite messages to show a user and have opposite
    fallbacks (nothing vs the archive)."""


# A page we will truncate to ~250KB anyway; without this a link to a disk image buffers the whole thing into RAM.
MAX_FETCH_BYTES = 10 * 1024 * 1024


P_BLOCKED_V4_NETS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),  # link-local incl. cloud metadata
    ipaddress.ip_network("100.64.0.0/10"),   # CGNAT
    ipaddress.ip_network("224.0.0.0/4"),     # multicast
    ipaddress.ip_network("0.0.0.0/8"),       # "this network"
    ipaddress.ip_network("198.18.0.0/15"),   # benchmarking
]

P_BLOCKED_V6_NETS = [
    ipaddress.ip_network("fe80::/10"),       # link-local
    ipaddress.ip_network("fc00::/7"),        # ULA
    ipaddress.ip_network("ff00::/8"),        # multicast
    ipaddress.ip_network("::/128"),          # unspecified
]


async def p_resolve_host_async(host: str) -> list[str]:
    """Resolve host to all IPs (v4 + v6) without blocking the event loop."""
    loop = asyncio.get_event_loop()
    try:
        infos = await loop.getaddrinfo(host, None)
    except OSError as e:
        raise DomainUnreachable(f"{host} could not be resolved (dead domain, typo, or no network): {e}") from e
    return list({info[4][0] for info in infos})


def p_is_forbidden_ip(ip_str: str) -> bool:
    """True iff this IP is in a blocked range. Loopback is allowed (see module docstring)."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True  # unparseable -> block
    # v6 can carry a v4 target (v4-mapped ::ffff:, 6to4 2002::) and routes to it; judge by the embedded v4 or a private host slips past the v6 list.
    if ip.version == 6:
        embedded = ip.ipv4_mapped or ip.sixtofour
        if embedded is not None:
            ip = embedded
    if ip.is_loopback:
        return False
    if ip.version == 4:
        return any(ip in net for net in P_BLOCKED_V4_NETS)
    return any(ip in net for net in P_BLOCKED_V6_NETS)


async def assert_safe_url(url: str) -> str:
    """Raise SSRFBlocked if url targets a forbidden range; otherwise return url.

    Resolves the host to ALL records (multi-A defense against single-record
    rebinding) and rejects if ANY resolution is private. Does not perfectly close
    DNS-rebinding TOCTOU (httpx resolves again on connect), but the agent-fetcher
    threat model on a desktop app is dominated by cloud-metadata and internal-LAN
    targets, not active rebinding attacks.
    """
    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        raise SSRFBlocked(f"Unsupported URL scheme {scheme!r}; only http/https allowed.")
    host = parsed.hostname
    if not host:
        raise SSRFBlocked("URL has no hostname.")

    try:
        ipaddress.ip_address(host)
        if p_is_forbidden_ip(host):
            raise SSRFBlocked(f"URL host {host} is in a blocked range.")
        return url
    except ValueError:
        pass

    resolved = await p_resolve_host_async(host)
    if not resolved:
        raise DomainUnreachable(f"No DNS records for {host}.")
    for ip in resolved:
        if p_is_forbidden_ip(ip):
            raise SSRFBlocked(f"Host {host} resolves to forbidden IP {ip}.")
    return url


async def p_read_capped(client: httpx.AsyncClient, request: httpx.Request,
                        max_bytes: int) -> httpx.Response:
    """Send `request` and buffer at most `max_bytes` of the body.

    Returns a detached Response so callers keep the plain `.content` / `.text`
    interface. Content-Encoding and Content-Length are dropped because
    `aiter_bytes` already yields decoded bytes and the count may be short.
    """
    streamed = await client.send(request, stream=True)
    chunks: list[bytes] = []
    total = 0
    try:
        async for chunk in streamed.aiter_bytes():
            chunks.append(chunk)
            total += len(chunk)
            if total >= max_bytes:
                break
    finally:
        await streamed.aclose()
    headers = httpx.Headers(
        [(k, v) for k, v in streamed.headers.multi_items()
         if k.lower() not in ("content-encoding", "content-length")]
    )
    return httpx.Response(status_code=streamed.status_code, headers=headers,
                          content=b"".join(chunks)[:max_bytes], request=request)


async def safe_fetch(
    url: str,
    *,
    method: str = "GET",
    headers: dict | None = None,
    timeout: float = 30.0,
    max_redirects: int = 5,
    json_body: dict | None = None,
    data: dict | None = None,
    max_bytes: int = MAX_FETCH_BYTES,
) -> httpx.Response:
    """Fetch with per-redirect SSRF re-validation.

    Manually walks the redirect chain so each hop's target host is re-checked,
    closing the per-redirect SSRF window that follow_redirects=True leaves open.
    """
    current_url = await assert_safe_url(url)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False, headers=headers or {}) as client:
        for _ in range(max_redirects + 1):
            req_kwargs: dict = {}
            if method.upper() == "POST":
                if json_body is not None:
                    req_kwargs["json"] = json_body
                if data is not None:
                    req_kwargs["data"] = data
            request = client.build_request(method.upper(), current_url, **req_kwargs)
            resp = await p_read_capped(client, request, max_bytes)
            if not (300 <= resp.status_code < 400):
                return resp
            location = resp.headers.get("location")
            if not location:
                return resp
            next_url = urljoin(current_url, location)
            current_url = await assert_safe_url(next_url)
    raise SSRFBlocked(f"Too many redirects (> {max_redirects}) starting from {url}.")
