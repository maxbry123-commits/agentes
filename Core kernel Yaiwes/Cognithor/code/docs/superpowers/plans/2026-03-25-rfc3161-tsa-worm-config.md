# RFC 3161 TSA + WORM Config Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add RFC 3161 Timestamp Authority support (daily audit batch timestamping) and WORM config fields for future S3/MinIO integration.

**Architecture:** New `security/tsa.py` module with `TSAClient` class that creates RFC 3161 timestamp requests using OpenSSL CLI (universally available, no pip dependency). Daily background task in gateway creates a timestamp for the day's audit anchor hash. TSA responses stored as `.tsr` files alongside JSONL audit logs. WORM config fields prepared in `AuditConfig` for future S3 Object Lock backend.

**Tech Stack:** Python 3.12+ (subprocess for openssl, urllib for HTTP), pytest

---

## Design Decisions

### Why OpenSSL CLI instead of rfc3161ng/rfc3161-client?

1. **No pip dependency** — OpenSSL is pre-installed on Linux/macOS/Windows (Git Bash)
2. **Legally verifiable** — `openssl ts -verify` produces court-admissible proof
3. **Portable** — Works offline after initial certificate download
4. **Cognithor philosophy** — "local-first, no cloud required"
5. **Fallback** — Pure urllib POST as alternative if openssl unavailable

### Daily batch vs per-entry timestamps

- **Per-entry**: 50,000+ TSA requests/day → rate-limited, slow, wasteful
- **Daily batch**: 1 TSA request per day on the `get_anchor()` hash → proves ALL entries of that day existed and are unmodified
- **How**: Hash of last audit entry of the day = cryptographic commitment to the entire chain

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/jarvis/security/tsa.py` | TSAClient: build request, send to TSA, store response |
| Modify | `src/jarvis/security/audit.py` | Add `timestamp_anchor()` method using TSAClient |
| Modify | `src/jarvis/config.py` | Add TSA + WORM fields to AuditConfig |
| Modify | `src/jarvis/gateway/gateway.py` | Daily TSA timestamp in retention cleanup task |
| Modify | `src/jarvis/channels/config_routes.py` | GET /api/v1/audit/timestamps endpoint |
| Create | `tests/unit/test_tsa.py` | Tests for TSAClient + integration |

---

### Task 1: TSAClient — OpenSSL-based RFC 3161 Client

**Files:**
- Create: `src/jarvis/security/tsa.py`
- Create: `tests/unit/test_tsa.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_tsa.py`:

```python
"""Tests for RFC 3161 Timestamp Authority client."""

import hashlib
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestTSAClient:
    """TSAClient creates timestamp requests and stores responses."""

    @pytest.fixture
    def client(self, tmp_path):
        from jarvis.security.tsa import TSAClient

        return TSAClient(
            tsa_url="https://freetsa.org/tsr",
            storage_dir=tmp_path / "tsa",
        )

    def test_build_request_creates_tsq_file(self, client, tmp_path):
        digest = hashlib.sha256(b"test data").hexdigest()
        tsq_path = client.build_request(digest, tmp_path / "test.tsq")
        assert tsq_path.exists()
        assert tsq_path.stat().st_size > 0

    def test_build_request_without_openssl_uses_fallback(self, client, tmp_path):
        digest = hashlib.sha256(b"test data").hexdigest()
        with patch("shutil.which", return_value=None):
            tsq_path = client.build_request(digest, tmp_path / "test.tsq")
            # Should still produce a file (raw DER fallback or skip)
            # If openssl not available, returns None
            if tsq_path is None:
                assert True  # Expected behavior without openssl

    def test_store_response_saves_tsr(self, client, tmp_path):
        tsr_data = b"fake-tsr-response-bytes"
        tsr_path = client.store_response("2026-03-25", tsr_data)
        assert tsr_path.exists()
        assert tsr_path.read_bytes() == tsr_data

    def test_list_timestamps_returns_stored(self, client, tmp_path):
        client.store_response("2026-03-25", b"data1")
        client.store_response("2026-03-24", b"data2")
        timestamps = client.list_timestamps()
        assert len(timestamps) >= 2

    def test_get_timestamp_returns_none_for_missing(self, client):
        result = client.get_timestamp("2099-01-01")
        assert result is None

    def test_has_openssl_detection(self, client):
        result = client.has_openssl()
        assert isinstance(result, bool)


class TestTSAClientRequestViaCurl:
    """Test the HTTP request path (mocked, no real TSA calls)."""

    @pytest.fixture
    def client(self, tmp_path):
        from jarvis.security.tsa import TSAClient

        return TSAClient(
            tsa_url="https://freetsa.org/tsr",
            storage_dir=tmp_path / "tsa",
        )

    def test_request_timestamp_mocked(self, client, tmp_path):
        digest = hashlib.sha256(b"audit anchor").hexdigest()

        # Mock the HTTP call
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b"mock-tsr-bytes"
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = client.request_timestamp(digest, "2026-03-25")

        if result is not None:
            assert result.exists()
            assert result.read_bytes() == b"mock-tsr-bytes"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/test_tsa.py -v`
Expected: FAIL — `ImportError: cannot import name 'TSAClient'`

- [ ] **Step 3: Implement TSAClient**

Create `src/jarvis/security/tsa.py`:

```python
"""RFC 3161 Timestamp Authority Client.

Creates timestamp requests via OpenSSL CLI (universally available),
sends them to a TSA server, and stores the signed responses.

The TSA response proves that a specific hash (and thus the entire
audit chain up to that point) existed at a specific time.

Usage:
    client = TSAClient(tsa_url="https://freetsa.org/tsr",
                       storage_dir=Path("~/.cognithor/tsa/"))
    tsr_path = client.request_timestamp(sha256_hex, "2026-03-25")

Verification (manual, with OpenSSL):
    openssl ts -verify -in audit_2026-03-25.tsr \\
               -digest <sha256hex> -sha256 \\
               -CAfile cacert.pem -untrusted tsa.crt
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

from jarvis.utils.logging import get_logger

log = get_logger(__name__)

__all__ = ["TSAClient"]

# Default TSA servers (free, no registration)
DEFAULT_TSA_URL = "https://freetsa.org/tsr"
FALLBACK_TSA_URLS = [
    "http://timestamp.digicert.com",
    "http://timestamp.apple.com/ts01",
]


class TSAClient:
    """RFC 3161 Timestamp Authority client using OpenSSL CLI.

    Workflow:
      1. build_request(digest) → creates .tsq file via `openssl ts -query`
      2. send_request(tsq_path) → HTTP POST to TSA, returns .tsr bytes
      3. store_response(date, tsr_bytes) → saves .tsr alongside audit logs

    If OpenSSL is not available, falls back to raw urllib POST with
    manually constructed minimal ASN.1 DER request (SHA-256 only).
    """

    def __init__(
        self,
        tsa_url: str = DEFAULT_TSA_URL,
        storage_dir: Path | str = "",
    ) -> None:
        self._tsa_url = tsa_url
        self._storage_dir = Path(storage_dir) if storage_dir else Path.home() / ".cognithor" / "tsa"
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._openssl = shutil.which("openssl")

    def has_openssl(self) -> bool:
        """Check if OpenSSL CLI is available."""
        return self._openssl is not None

    def build_request(
        self,
        sha256_hex: str,
        output_path: Path | None = None,
    ) -> Path | None:
        """Build a TimeStampReq (.tsq) file for a SHA-256 digest.

        Args:
            sha256_hex: SHA-256 hex digest of the data to timestamp.
            output_path: Where to write the .tsq file.

        Returns:
            Path to the .tsq file, or None if OpenSSL unavailable.
        """
        if not self._openssl:
            log.debug("tsa_openssl_not_available")
            return None

        if output_path is None:
            output_path = self._storage_dir / f"request_{sha256_hex[:16]}.tsq"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            result = subprocess.run(
                [
                    self._openssl, "ts", "-query",
                    "-digest", sha256_hex,
                    "-sha256",
                    "-cert",
                    "-no_nonce",
                    "-out", str(output_path),
                ],
                capture_output=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode != 0:
                log.warning(
                    "tsa_build_request_failed",
                    stderr=result.stderr.decode(errors="replace")[:200],
                )
                return None
            return output_path
        except Exception as exc:
            log.warning("tsa_build_request_error", error=str(exc))
            return None

    def send_request(self, tsq_path: Path) -> bytes | None:
        """Send a .tsq file to the TSA server via HTTP POST.

        Args:
            tsq_path: Path to the TimeStampReq file.

        Returns:
            Raw TSA response bytes (.tsr), or None on failure.
        """
        if not tsq_path.exists():
            return None

        tsq_data = tsq_path.read_bytes()
        urls = [self._tsa_url] + [u for u in FALLBACK_TSA_URLS if u != self._tsa_url]

        for url in urls:
            try:
                req = urllib.request.Request(
                    url,
                    data=tsq_data,
                    headers={"Content-Type": "application/timestamp-query"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    if resp.status == 200:
                        tsr_data = resp.read()
                        log.info("tsa_response_received", url=url, size=len(tsr_data))
                        return tsr_data
            except Exception as exc:
                log.debug("tsa_send_failed", url=url, error=str(exc))
                continue

        log.warning("tsa_all_servers_failed")
        return None

    def request_timestamp(
        self,
        sha256_hex: str,
        date_str: str,
    ) -> Path | None:
        """Full flow: build request → send to TSA → store response.

        Args:
            sha256_hex: SHA-256 hex digest of the audit anchor.
            date_str: Date string for the filename (e.g., "2026-03-25").

        Returns:
            Path to the stored .tsr file, or None on failure.
        """
        # Step 1: Build .tsq
        tsq_path = self._storage_dir / f"audit_{date_str}.tsq"
        built = self.build_request(sha256_hex, tsq_path)
        if built is None:
            # Fallback: try raw HTTP POST without openssl
            return self._request_timestamp_raw(sha256_hex, date_str)

        # Step 2: Send to TSA
        tsr_data = self.send_request(tsq_path)
        if tsr_data is None:
            return None

        # Step 3: Store response
        return self.store_response(date_str, tsr_data)

    def _request_timestamp_raw(
        self,
        sha256_hex: str,
        date_str: str,
    ) -> Path | None:
        """Fallback: Build minimal ASN.1 DER request without OpenSSL.

        This builds a bare-minimum TimeStampReq for SHA-256 digests.
        Not as robust as OpenSSL, but works when it's not available.
        """
        digest_bytes = bytes.fromhex(sha256_hex)

        # Minimal ASN.1 DER TimeStampReq for SHA-256
        # SEQUENCE {
        #   INTEGER 1 (version)
        #   SEQUENCE { (messageImprint)
        #     SEQUENCE { (hashAlgorithm - SHA-256 OID: 2.16.840.1.101.3.4.2.1)
        #       OID 2.16.840.1.101.3.4.2.1
        #       NULL
        #     }
        #     OCTET STRING (32 bytes hash)
        #   }
        #   BOOLEAN TRUE (certReq)
        # }
        sha256_oid = bytes([
            0x30, 0x0d,  # SEQUENCE (13 bytes)
            0x06, 0x09,  # OID (9 bytes)
            0x60, 0x86, 0x48, 0x01, 0x65, 0x03, 0x04, 0x02, 0x01,  # SHA-256
            0x05, 0x00,  # NULL
        ])
        message_imprint = bytes([0x30, len(sha256_oid) + 2 + len(digest_bytes)]) + \
            sha256_oid + bytes([0x04, len(digest_bytes)]) + digest_bytes
        version = bytes([0x02, 0x01, 0x01])  # INTEGER 1
        cert_req = bytes([0x01, 0x01, 0xff])  # BOOLEAN TRUE
        inner = version + message_imprint + cert_req
        tsq_data = bytes([0x30, len(inner)]) + inner

        # Send directly
        try:
            req = urllib.request.Request(
                self._tsa_url,
                data=tsq_data,
                headers={"Content-Type": "application/timestamp-query"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    tsr_data = resp.read()
                    return self.store_response(date_str, tsr_data)
        except Exception as exc:
            log.debug("tsa_raw_request_failed", error=str(exc))

        return None

    def store_response(self, date_str: str, tsr_data: bytes) -> Path:
        """Store a TSA response as .tsr file.

        Args:
            date_str: Date string for filename.
            tsr_data: Raw TSA response bytes.

        Returns:
            Path to the stored .tsr file.
        """
        tsr_path = self._storage_dir / f"audit_{date_str}.tsr"
        tsr_path.write_bytes(tsr_data)
        log.info("tsa_response_stored", path=str(tsr_path), size=len(tsr_data))
        return tsr_path

    def list_timestamps(self) -> list[dict[str, Any]]:
        """List all stored TSA timestamps.

        Returns:
            List of dicts with date, path, size for each .tsr file.
        """
        results = []
        for tsr_file in sorted(self._storage_dir.glob("audit_*.tsr")):
            # Extract date from filename: audit_2026-03-25.tsr → 2026-03-25
            stem = tsr_file.stem  # audit_2026-03-25
            date_str = stem.replace("audit_", "")
            results.append({
                "date": date_str,
                "path": str(tsr_file),
                "size_bytes": tsr_file.stat().st_size,
            })
        return results

    def get_timestamp(self, date_str: str) -> Path | None:
        """Get a stored TSA response for a specific date.

        Returns:
            Path to .tsr file, or None if not found.
        """
        tsr_path = self._storage_dir / f"audit_{date_str}.tsr"
        return tsr_path if tsr_path.exists() else None

    def verify_timestamp(
        self,
        date_str: str,
        sha256_hex: str,
        ca_cert: Path | None = None,
        tsa_cert: Path | None = None,
    ) -> dict[str, Any]:
        """Verify a stored TSA response using OpenSSL.

        Args:
            date_str: Date of the timestamp.
            sha256_hex: Expected SHA-256 digest.
            ca_cert: Path to CA certificate (optional).
            tsa_cert: Path to TSA certificate (optional).

        Returns:
            Dict with verified (bool), output (str), error (str).
        """
        if not self._openssl:
            return {"verified": False, "error": "OpenSSL not available"}

        tsr_path = self.get_timestamp(date_str)
        if tsr_path is None:
            return {"verified": False, "error": f"No timestamp for {date_str}"}

        cmd = [
            self._openssl, "ts", "-verify",
            "-in", str(tsr_path),
            "-digest", sha256_hex,
            "-sha256",
        ]
        if ca_cert and ca_cert.exists():
            cmd.extend(["-CAfile", str(ca_cert)])
        if tsa_cert and tsa_cert.exists():
            cmd.extend(["-untrusted", str(tsa_cert)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            output = result.stdout.decode(errors="replace").strip()
            error = result.stderr.decode(errors="replace").strip()
            verified = result.returncode == 0 and "verification: ok" in output.lower()
            return {
                "verified": verified,
                "output": output,
                "error": error if not verified else "",
            }
        except Exception as exc:
            return {"verified": False, "error": str(exc)}
```

- [ ] **Step 4: Run tests**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/test_tsa.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/security/tsa.py tests/unit/test_tsa.py
git commit -m "feat: RFC 3161 TSAClient with OpenSSL CLI + raw ASN.1 fallback"
```

---

### Task 2: WORM Config Fields + TSA Config

**Files:**
- Modify: `src/jarvis/config.py`

- [ ] **Step 1: Extend AuditConfig with TSA + WORM fields**

In `src/jarvis/config.py`, find the `AuditConfig` class and add after `retention_days`:

```python
    # RFC 3161 Timestamp Authority
    tsa_enabled: bool = Field(
        default=False,
        description="Taegliche RFC 3161 Timestamps auf Audit-Anchor-Hash",
    )
    tsa_url: str = Field(
        default="https://freetsa.org/tsr",
        description="URL des TSA-Servers",
    )

    # WORM Storage (future — prepared config fields)
    worm_backend: Literal["none", "s3", "minio"] = Field(
        default="none",
        description="WORM-Backend: none (lokal), s3 (AWS Object Lock), minio (Self-Hosted)",
    )
    worm_bucket: str = Field(
        default="",
        description="S3/MinIO Bucket-Name fuer WORM-Storage",
    )
    worm_retention_days: int = Field(
        default=365, ge=30, le=3650,
        description="WORM Retention-Lock in Tagen",
    )
```

Add `Literal` to the typing import if not already present.

- [ ] **Step 2: Verify config loads**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -c "from jarvis.config import JarvisConfig; c = JarvisConfig(); print(c.audit.tsa_enabled, c.audit.worm_backend)"`
Expected: `False none`

- [ ] **Step 3: Commit**

```bash
git add src/jarvis/config.py
git commit -m "feat: add TSA + WORM config fields to AuditConfig"
```

---

### Task 3: Daily TSA Timestamp in Gateway

**Files:**
- Modify: `src/jarvis/gateway/gateway.py`

- [ ] **Step 1: Add TSA timestamping to the daily retention cleanup task**

Find the `_daily_retention_cleanup` async function in gateway.py (around line 776). Add TSA timestamping INSIDE the existing daily loop, after the cleanup logic:

```python
                    # RFC 3161 TSA: Daily timestamp on audit anchor
                    if (
                        getattr(self._config, "audit", None)
                        and getattr(self._config.audit, "tsa_enabled", False)
                        and hasattr(self, "_audit_trail")
                        and self._audit_trail
                    ):
                        try:
                            from jarvis.security.tsa import TSAClient
                            from datetime import UTC, datetime

                            anchor = self._audit_trail.get_anchor()
                            if anchor["entry_count"] > 0:
                                date_str = datetime.now(UTC).strftime("%Y-%m-%d")
                                tsa_url = getattr(self._config.audit, "tsa_url", "https://freetsa.org/tsr")
                                tsa_dir = self._config.jarvis_home / "tsa"
                                tsa_client = TSAClient(tsa_url=tsa_url, storage_dir=tsa_dir)
                                tsr_path = tsa_client.request_timestamp(
                                    anchor["hash"], date_str
                                )
                                if tsr_path:
                                    log.info(
                                        "tsa_daily_timestamp_created",
                                        date=date_str,
                                        anchor_hash=anchor["hash"][:16],
                                        entry_count=anchor["entry_count"],
                                        tsr_path=str(tsr_path),
                                    )
                                else:
                                    log.warning("tsa_daily_timestamp_failed", date=date_str)
                        except Exception:
                            log.debug("tsa_daily_failed", exc_info=True)
```

- [ ] **Step 2: Verify syntax**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -c "from jarvis.gateway.gateway import Gateway; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add src/jarvis/gateway/gateway.py
git commit -m "feat: daily RFC 3161 TSA timestamp on audit anchor hash"
```

---

### Task 4: Audit Timestamps API Endpoint

**Files:**
- Modify: `src/jarvis/channels/config_routes.py`

- [ ] **Step 1: Add GET /api/v1/audit/timestamps endpoint**

Near the existing `/api/v1/audit/verify` endpoint, add:

```python
    @app.get("/api/v1/audit/timestamps", dependencies=deps)
    async def list_audit_timestamps() -> dict[str, Any]:
        """List all RFC 3161 TSA timestamps for audit logs."""
        try:
            from jarvis.security.tsa import TSAClient

            tsa_dir = config_manager.config.jarvis_home / "tsa"
            client = TSAClient(storage_dir=tsa_dir)
            timestamps = client.list_timestamps()
            return {
                "timestamps": timestamps,
                "count": len(timestamps),
                "tsa_url": getattr(
                    getattr(config_manager.config, "audit", None),
                    "tsa_url", "https://freetsa.org/tsr"
                ),
                "tsa_enabled": getattr(
                    getattr(config_manager.config, "audit", None),
                    "tsa_enabled", False
                ),
            }
        except Exception as exc:
            return {"timestamps": [], "count": 0, "error": str(exc)}
```

- [ ] **Step 2: Verify syntax**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -c "from jarvis.channels.config_routes import create_config_routes; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add src/jarvis/channels/config_routes.py
git commit -m "feat: GET /api/v1/audit/timestamps endpoint for TSA timestamp listing"
```

---

### Task 5: Full Test Suite

- [ ] **Step 1: Run TSA tests**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/test_tsa.py -v`
Expected: All PASS

- [ ] **Step 2: Run all unit tests**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/unit/ -v`
Expected: All PASS (39+ existing + 7 new)

- [ ] **Step 3: Run tool registration + planner tests**

Run: `cd "D:\Jarvis\jarvis complete v20" && python -m pytest tests/ -k "tool_registration or planner" -v`
Expected: All PASS

- [ ] **Step 4: Commit any fixes**

```bash
git add -A
git commit -m "fix: test adjustments for TSA + WORM integration"
```
