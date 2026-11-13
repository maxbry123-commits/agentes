"""Tests for S3/MinIO WORM storage backend."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers: create a minimal AuditConfig-like object
# ---------------------------------------------------------------------------


class _FakeAuditConfig:
    def __init__(
        self,
        worm_backend: str = "s3",
        worm_bucket: str = "test-bucket",
        worm_retention_days: int = 365,
    ):
        self.worm_backend = worm_backend
        self.worm_bucket = worm_bucket
        self.worm_retention_days = worm_retention_days


def _make_audit_file(audit_dir: Path, name: str = "audit_2026-03-25.jsonl") -> Path:
    """Create a small fake audit JSONL file."""
    p = audit_dir / name
    p.write_text('{"entry_id":"audit_1","action":"test"}\n', encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def cognithor_home(tmp_path: Path) -> Path:
    home = tmp_path / ".cognithor"
    home.mkdir()
    return home


@pytest.fixture()
def audit_dir(tmp_path: Path) -> Path:
    d = tmp_path / "audit"
    d.mkdir()
    return d


# ---------------------------------------------------------------------------
# 1. Upload with mocked S3
# ---------------------------------------------------------------------------


@patch("cognithor.audit.worm._HAS_BOTO3", True)
@patch("cognithor.audit.worm.boto3")
def test_upload_daily_with_mock_s3(
    mock_boto3: MagicMock,
    cognithor_home: Path,
    audit_dir: Path,
) -> None:
    """PutObject is called with correct Object Lock params."""
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client

    from cognithor.audit.worm import WORMUploader

    cfg = _FakeAuditConfig(worm_backend="s3", worm_bucket="my-audit")
    uploader = WORMUploader(cfg, cognithor_home)

    _make_audit_file(audit_dir, "audit_2026-03-25.jsonl")

    uploaded = uploader.upload_daily(audit_dir)

    assert uploaded == ["audit_2026-03-25.jsonl"]
    assert mock_client.put_object.call_count == 1

    call_kwargs = mock_client.put_object.call_args[1]
    assert call_kwargs["Bucket"] == "my-audit"
    assert call_kwargs["Key"] == "audit/audit_2026-03-25.jsonl"
    assert call_kwargs["ObjectLockMode"] == "COMPLIANCE"
    assert "ObjectLockRetainUntilDate" in call_kwargs

    # Retention date should be ~365 days from now
    retain = call_kwargs["ObjectLockRetainUntilDate"]
    assert isinstance(retain, datetime)
    delta = retain - datetime.now(UTC)
    assert 360 < delta.days <= 366


# ---------------------------------------------------------------------------
# 2. Skip already-uploaded files
# ---------------------------------------------------------------------------


@patch("cognithor.audit.worm._HAS_BOTO3", True)
@patch("cognithor.audit.worm.boto3")
def test_skip_already_uploaded(
    mock_boto3: MagicMock,
    cognithor_home: Path,
    audit_dir: Path,
) -> None:
    """Files already in state DB are not re-uploaded."""
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client

    from cognithor.audit.worm import WORMUploader

    cfg = _FakeAuditConfig()
    uploader = WORMUploader(cfg, cognithor_home)

    _make_audit_file(audit_dir, "audit_2026-03-24.jsonl")
    _make_audit_file(audit_dir, "audit_2026-03-25.jsonl")

    # First upload — both files
    first = uploader.upload_daily(audit_dir)
    assert len(first) == 2
    assert mock_client.put_object.call_count == 2

    # Second upload — nothing new
    mock_client.put_object.reset_mock()
    second = uploader.upload_daily(audit_dir)
    assert second == []
    assert mock_client.put_object.call_count == 0


# ---------------------------------------------------------------------------
# 3. list_uploaded returns state DB contents
# ---------------------------------------------------------------------------


@patch("cognithor.audit.worm._HAS_BOTO3", True)
@patch("cognithor.audit.worm.boto3")
def test_list_uploaded(
    mock_boto3: MagicMock,
    cognithor_home: Path,
    audit_dir: Path,
) -> None:
    """list_uploaded() reflects the state DB after uploading."""
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client

    from cognithor.audit.worm import WORMUploader

    cfg = _FakeAuditConfig()
    uploader = WORMUploader(cfg, cognithor_home)

    _make_audit_file(audit_dir, "audit_2026-03-25.jsonl")
    uploader.upload_daily(audit_dir)

    entries = uploader.list_uploaded()
    assert len(entries) == 1
    assert entries[0]["filename"] == "audit_2026-03-25.jsonl"
    assert entries[0]["bucket"] == "test-bucket"
    assert entries[0]["key"] == "audit/audit_2026-03-25.jsonl"
    assert entries[0]["retention_until"]  # non-empty string


# ---------------------------------------------------------------------------
# 4. Graceful when boto3 is not installed
# ---------------------------------------------------------------------------


def test_graceful_without_boto3(cognithor_home: Path, audit_dir: Path) -> None:
    """No crash when boto3 is missing — upload_daily returns []."""
    _make_audit_file(audit_dir)

    with patch("cognithor.audit.worm._HAS_BOTO3", False):
        from cognithor.audit.worm import WORMUploader

        cfg = _FakeAuditConfig(worm_backend="s3")
        uploader = WORMUploader(cfg, cognithor_home)
        result = uploader.upload_daily(audit_dir)

    assert result == []


# ---------------------------------------------------------------------------
# 5. MinIO uses custom endpoint_url
# ---------------------------------------------------------------------------


@patch("cognithor.audit.worm._HAS_BOTO3", True)
@patch("cognithor.audit.worm.boto3")
def test_minio_uses_custom_endpoint(
    mock_boto3: MagicMock,
    cognithor_home: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MinIO backend passes endpoint_url from MINIO_ENDPOINT_URL."""
    monkeypatch.setenv("MINIO_ENDPOINT_URL", "http://minio.local:9000")

    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client

    from cognithor.audit.worm import WORMUploader

    cfg = _FakeAuditConfig(worm_backend="minio", worm_bucket="minio-audit")
    _uploader = WORMUploader(cfg, cognithor_home)

    # boto3.client() should have been called with endpoint_url
    mock_boto3.client.assert_called_once_with(
        service_name="s3",
        endpoint_url="http://minio.local:9000",
    )
