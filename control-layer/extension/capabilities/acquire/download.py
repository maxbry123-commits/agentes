"""DOWNLOAD · SHA256 · Range chunks when large.

GitHub soft limit ~100MiB for some paths; we stream to disk and
use HTTP Range when Accept-Ranges and size > CHUNK_THRESHOLD.
"""
from __future__ import annotations

import hashlib
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .rate_governor import RateGovernor

CHUNK_THRESHOLD = 32 * 1024 * 1024  # 32 MiB
CHUNK_SIZE = 16 * 1024 * 1024       # 16 MiB


@dataclass
class DownloadResult:
    ok: bool
    path: str | None = None
    sha256: str | None = None
    size: int = 0
    error: str | None = None
    method: str = "GET"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _cache_path(dest: Path, hexdigest: str) -> Path:
    return dest.parent.parent / "cache" / "sha256" / hexdigest[:2] / hexdigest[2:4] / hexdigest


def download_url(
    url: str,
    dest: Path,
    *,
    token: str | None = None,
    expected_sha256: str | None = None,
    max_bytes: int = 0,
    governor: RateGovernor | None = None,
    chunk_threshold: int = CHUNK_THRESHOLD,
    chunk_size: int = CHUNK_SIZE,
) -> DownloadResult:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    gov = governor or RateGovernor()

    if expected_sha256:
        hexdigest = expected_sha256.replace("sha256:", "")
        cache = _cache_path(dest, hexdigest)
        if cache.is_file():
            if not dest.exists():
                dest.write_bytes(cache.read_bytes())
            return DownloadResult(True, str(dest), hexdigest, cache.stat().st_size, method="CACHE")

    if not gov.acquire_slot():
        return DownloadResult(False, error="rate_limited")

    headers = {"User-Agent": "wordflow-acquire/0.1"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        size_hint = 0
        accept = ""
        try:
            req = urllib.request.Request(url, method="HEAD", headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                gov.observe_headers(resp.headers, resp.status)
                cl = resp.headers.get("Content-Length")
                accept = (resp.headers.get("Accept-Ranges") or "").lower()
                size_hint = int(cl) if cl and cl.isdigit() else 0
        except Exception:
            pass

        if max_bytes and size_hint and size_hint > max_bytes:
            return DownloadResult(False, error=f"too_large:{size_hint}>{max_bytes}")

        use_range = ("bytes" in accept) and size_hint > chunk_threshold
        if use_range:
            return _download_chunked(
                url, dest, headers, gov,
                total=size_hint, chunk_size=chunk_size,
                expected_sha256=expected_sha256,
            )

        # stream full GET to disk (avoid holding huge blobs in RAM when possible)
        req = urllib.request.Request(url, headers=headers)
        h = hashlib.sha256()
        size = 0
        with urllib.request.urlopen(req, timeout=300) as resp:
            gov.observe_headers(resp.headers, resp.status)
            with open(dest, "wb") as out:
                while True:
                    block = resp.read(1024 * 1024)
                    if not block:
                        break
                    out.write(block)
                    h.update(block)
                    size += len(block)
                    if max_bytes and size > max_bytes:
                        return DownloadResult(False, str(dest), error=f"too_large_stream:{size}")
        digest = h.hexdigest()
        if expected_sha256:
            exp = expected_sha256.replace("sha256:", "")
            if digest != exp:
                return DownloadResult(False, str(dest), digest, size, error="sha256_mismatch")
        cache = _cache_path(dest, digest)
        cache.parent.mkdir(parents=True, exist_ok=True)
        if not cache.exists():
            cache.write_bytes(dest.read_bytes())
        return DownloadResult(True, str(dest), digest, size, method="GET_STREAM")
    except urllib.error.HTTPError as e:
        gov.observe_headers(e.headers or {}, e.code)
        return DownloadResult(False, error=f"http_{e.code}")
    except Exception as e:  # noqa: BLE001
        return DownloadResult(False, error=str(e))
    finally:
        gov.release_slot()


def _download_chunked(
    url: str,
    dest: Path,
    headers: dict[str, str],
    gov: RateGovernor,
    *,
    total: int,
    chunk_size: int,
    expected_sha256: str | None,
) -> DownloadResult:
    h = hashlib.sha256()
    offset = 0
    with open(dest, "wb") as out:
        while offset < total:
            end = min(offset + chunk_size - 1, total - 1)
            hdr = dict(headers)
            hdr["Range"] = f"bytes={offset}-{end}"
            req = urllib.request.Request(url, headers=hdr)
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    gov.observe_headers(resp.headers, resp.status)
                    if resp.status not in (200, 206):
                        return DownloadResult(False, error=f"range_status_{resp.status}")
                    block = resp.read()
            except urllib.error.HTTPError as e:
                return DownloadResult(False, error=f"range_http_{e.code}")
            out.write(block)
            h.update(block)
            offset += len(block)
            if len(block) == 0:
                break
    digest = h.hexdigest()
    size = dest.stat().st_size
    if expected_sha256:
        exp = expected_sha256.replace("sha256:", "")
        if digest != exp:
            return DownloadResult(False, str(dest), digest, size, error="sha256_mismatch")
    cache = _cache_path(dest, digest)
    cache.parent.mkdir(parents=True, exist_ok=True)
    if not cache.exists():
        cache.write_bytes(dest.read_bytes())
    return DownloadResult(True, str(dest), digest, size, method="RANGE_CHUNKED")
