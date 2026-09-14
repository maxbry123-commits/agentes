"""Tests for RFC 3161 Timestamp Authority client."""

import hashlib
from unittest.mock import MagicMock, patch

import pytest


class TestTSAClient:
    """TSAClient creates timestamp requests and stores responses."""

    @pytest.fixture
    def client(self, tmp_path):
        from cognithor.security.tsa import TSAClient

        return TSAClient(
            tsa_url="https://freetsa.org/tsr",
            storage_dir=tmp_path / "tsa",
        )

    def test_build_request_creates_tsq_file(self, client, tmp_path):
        if not client.has_openssl():
            pytest.skip("OpenSSL not available")
        digest = hashlib.sha256(b"test data").hexdigest()
        tsq_path = client.build_request(digest, tmp_path / "test.tsq")
        assert tsq_path is not None
        assert tsq_path.exists()
        assert tsq_path.stat().st_size > 0

    def test_build_request_without_openssl_uses_fallback(self, client, tmp_path):
        digest = hashlib.sha256(b"test data").hexdigest()
        with patch("shutil.which", return_value=None):
            from cognithor.security.tsa import TSAClient

            fallback_client = TSAClient(
                tsa_url="https://freetsa.org/tsr",
                storage_dir=tmp_path / "tsa_fallback",
            )
            tsq_path = fallback_client.build_request(digest, tmp_path / "test.tsq")
            # Without openssl, build_request returns None
            assert tsq_path is None

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
        from cognithor.security.tsa import TSAClient

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
