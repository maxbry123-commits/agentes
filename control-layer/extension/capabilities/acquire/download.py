"""DOWNLOAD · verify SHA256 · minimal Range support.
"""
from __future__ import annotations

import hashlib
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .rate_governor import RateGovernor


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


def download_url(
    url: str,
    dest: Path,
    *,
    token: str | None = None,
    expected_sha256: str | None = None,
    max_bytes: int = 0,
    governor: RateGovernor | None = None,
) -> DownloadResult:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    gov = governor or RateGovernor()

    # artifact cache by expected sha
    if expected_sha256:
        hexdigest = expected_sha256.replace("sha256:", "")
        cache = dest.parent.parent / "cache" / "sha256" / hexdigest[:2] / hexdigest[2:4] / hexdigest
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
        # probe
        req = urllib.request.Request(url, method="HEAD", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                gov.observe_headers(resp.headers, resp.status)
                cl = resp.headers.get("Content-Length")
                accept = (resp.headers.get("Accept-Ranges") or "").lower()
                size_hint = int(cl) if cl and cl.isdigit() else 0
        except Exception:
            size_hint = 0
            accept = ""

        if max_bytes and size_hint and size_hint > max_bytes:
            return DownloadResult(False, error=f"too_large:{size_hint}>{max_bytes}")

        # full GET (Range path can be added later per chunk node)
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=120) as resp:
            gov.observe_headers(resp.headers, resp.status)
            data = resp.read()
        dest.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        if expected_sha256:
            exp = expected_sha256.replace("sha256:", "")
            if digest != exp:
                return DownloadResult(False, str(dest), digest, len(data), error="sha256_mismatch")
        # write cache
        cache = dest.parent.parent / "cache" / "sha256" / digest[:2] / digest[2:4] / digest
        cache.parent.mkdir(parents=True, exist_ok=True)
        if not cache.exists():
            cache.write_bytes(data)
        return DownloadResult(True, str(dest), digest, len(data), method="GET" + ("+rangeable" if "bytes" in accept else ""))
    except urllib.error.HTTPError as e:
        gov.observe_headers(e.headers or {}, e.code)
        return DownloadResult(False, error=f"http_{e.code}")
    except Exception as e:  # noqa: BLE001
        return DownloadResult(False, error=str(e))
    finally:
        gov.release_slot()
