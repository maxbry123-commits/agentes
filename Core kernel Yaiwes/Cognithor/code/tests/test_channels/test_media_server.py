from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from cognithor.channels.media_server import MediaUploadServer
from cognithor.config import CognithorConfig, VLLMConfig
from cognithor.core.llm_backend import (
    MediaUploadTooLargeError,
    MediaUploadUnsupportedFormatError,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def server(tmp_path: Path) -> MediaUploadServer:
    cfg = CognithorConfig(
        cognithor_home=tmp_path,
        vllm=VLLMConfig(
            enabled=True,
            video_max_upload_mb=10,  # small cap for fast tests
            video_quota_gb=1,
        ),
    )
    srv = MediaUploadServer(cfg)
    # Pretend we've bound to port 4711 (real start() is tested in Task 7)
    srv._port = 4711
    return srv


class TestSaveUpload:
    def test_saves_bytes_returns_uuid(self, server: MediaUploadServer):
        data = b"\x00" * 1024  # 1 KB
        uuid = server.save_upload(data, "mp4")
        assert uuid
        path = server._media_dir / f"{uuid}.mp4"
        assert path.is_file()
        assert path.read_bytes() == data

    def test_rejects_file_over_per_file_cap(self, server: MediaUploadServer):
        too_big = b"\x00" * (11 * 1024 * 1024)  # 11 MB > 10 MB cap
        with pytest.raises(MediaUploadTooLargeError):
            server.save_upload(too_big, "mp4")

    def test_rejects_unsupported_extension(self, server: MediaUploadServer):
        with pytest.raises(MediaUploadUnsupportedFormatError):
            server.save_upload(b"\x00" * 1024, "exe")

    def test_case_insensitive_extension(self, server: MediaUploadServer):
        uuid = server.save_upload(b"\x00" * 1024, "MP4")
        assert uuid  # accepts "MP4" / "Mp4"

    def test_public_url_shape(self, server: MediaUploadServer):
        uuid = server.save_upload(b"\x00" * 1024, "mp4")
        url = server.public_url(uuid, "mp4")
        assert url == f"http://host.docker.internal:4711/media/{uuid}.mp4"

    def test_lru_eviction_when_quota_exceeded(self, server: MediaUploadServer, tmp_path: Path):
        # Quota is 1 GB. Fill up with 3 files of 3 MB each.
        # Then add a file that would push total over a (monkey-patched) 12 MB quota.
        server._quota_bytes = 12 * 1024 * 1024  # override quota to 12 MB

        import time

        u1 = server.save_upload(b"\x00" * (3 * 1024 * 1024), "mp4")
        time.sleep(0.01)  # ensure distinct mtimes
        u2 = server.save_upload(b"\x00" * (3 * 1024 * 1024), "mp4")
        time.sleep(0.01)
        _ = server.save_upload(b"\x00" * (3 * 1024 * 1024), "mp4")

        # Now save a 5 MB file — total would be 14 MB > 12 MB quota.
        # Expected: u1 (oldest) gets evicted.
        u4 = server.save_upload(b"\x00" * (5 * 1024 * 1024), "mp4")
        assert not (server._media_dir / f"{u1}.mp4").exists()
        assert (server._media_dir / f"{u2}.mp4").exists()
        assert (server._media_dir / f"{u4}.mp4").exists()


class TestDelete:
    def test_delete_removes_file(self, server: MediaUploadServer):
        uuid = server.save_upload(b"\x00" * 1024, "mp4")
        path = server._media_dir / f"{uuid}.mp4"
        assert path.exists()
        server.delete(uuid, "mp4")
        assert not path.exists()

    def test_delete_of_missing_is_noop(self, server: MediaUploadServer):
        server.delete("nonexistent-uuid-abc", "mp4")  # must not raise


class TestLifecycle:
    @pytest.mark.asyncio
    async def test_start_binds_ephemeral_port_serves_media(self, tmp_path: Path):
        import httpx

        from cognithor.config import CognithorConfig, VLLMConfig

        cfg = CognithorConfig(
            cognithor_home=tmp_path,
            vllm=VLLMConfig(enabled=True, video_max_upload_mb=10, video_quota_gb=1),
        )
        srv = MediaUploadServer(cfg)
        port = await srv.start()
        try:
            assert port > 0
            uuid = srv.save_upload(b"hello video world", "mp4")
            url = f"http://127.0.0.1:{port}/media/{uuid}.mp4"
            async with httpx.AsyncClient() as client:
                r = await client.get(url, timeout=5.0)
            assert r.status_code == 200
            assert r.content == b"hello video world"
        finally:
            await srv.stop()

    @pytest.mark.asyncio
    async def test_start_stop_is_idempotent(self, tmp_path: Path):
        from cognithor.config import CognithorConfig, VLLMConfig

        cfg = CognithorConfig(
            cognithor_home=tmp_path,
            vllm=VLLMConfig(enabled=True),
        )
        srv = MediaUploadServer(cfg)
        await srv.start()
        await srv.stop()
        await srv.stop()  # second stop must not raise
        # Restart on a fresh instance
        srv2 = MediaUploadServer(cfg)
        port2 = await srv2.start()
        assert port2 > 0
        await srv2.stop()


class TestServePathTraversal:
    @pytest.mark.asyncio
    async def test_serve_rejects_parent_traversal(self, tmp_path: Path):
        import httpx

        from cognithor.config import CognithorConfig, VLLMConfig

        cfg = CognithorConfig(
            cognithor_home=tmp_path,
            vllm=VLLMConfig(enabled=True, video_max_upload_mb=10, video_quota_gb=1),
        )
        srv = MediaUploadServer(cfg)
        port = await srv.start()
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"http://127.0.0.1:{port}/media/..%2F..%2Fetc%2Fpasswd",
                    timeout=5.0,
                )
            assert r.status_code in (400, 404)
        finally:
            await srv.stop()

    @pytest.mark.asyncio
    async def test_serve_rejects_backslash_traversal(self, tmp_path: Path):
        import httpx

        from cognithor.config import CognithorConfig, VLLMConfig

        cfg = CognithorConfig(
            cognithor_home=tmp_path,
            vllm=VLLMConfig(enabled=True, video_max_upload_mb=10, video_quota_gb=1),
        )
        srv = MediaUploadServer(cfg)
        port = await srv.start()
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"http://127.0.0.1:{port}/media/..%5C..%5Csecret.txt",
                    timeout=5.0,
                )
            assert r.status_code in (400, 404)
        finally:
            await srv.stop()

    @pytest.mark.asyncio
    async def test_serve_accepts_legitimate_uuid(self, tmp_path: Path):
        """After hardening, legit {uuid}.mp4 still works."""
        import httpx

        from cognithor.config import CognithorConfig, VLLMConfig

        cfg = CognithorConfig(
            cognithor_home=tmp_path,
            vllm=VLLMConfig(enabled=True, video_max_upload_mb=10, video_quota_gb=1),
        )
        srv = MediaUploadServer(cfg)
        port = await srv.start()
        try:
            uuid = srv.save_upload(b"legit video bytes", "mp4")
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"http://127.0.0.1:{port}/media/{uuid}.mp4",
                    timeout=5.0,
                )
            assert r.status_code == 200
            assert r.content == b"legit video bytes"
        finally:
            await srv.stop()


class TestSaveUploadConcurrency:
    def test_many_concurrent_saves_stay_within_quota(self, tmp_path: Path):
        """Many concurrent save_upload calls must not race past the quota
        check. Invariant: after all threads complete, media_dir total bytes
        is at or below quota.

        Without a lock, two or more threads can each compute `current` before
        the others write, both pass the "will fit" check, and then all write
        their bytes — leaving the directory above quota. Ten concurrent
        1 MB saves against a 6 MB quota reliably exercise the race.
        """
        import threading

        from cognithor.channels.media_server import MediaUploadServer
        from cognithor.config import CognithorConfig, VLLMConfig

        cfg = CognithorConfig(
            cognithor_home=tmp_path,
            vllm=VLLMConfig(
                enabled=True,
                video_max_upload_mb=10,
                video_quota_gb=1,
            ),
        )
        srv = MediaUploadServer(cfg)
        srv._port = 4711
        srv._quota_bytes = 6 * 1024 * 1024  # 6 MB quota for the test

        data = b"\x00" * (1 * 1024 * 1024)  # 1 MB each

        errors: list[Exception] = []

        def worker() -> None:
            try:
                srv.save_upload(data, "mp4")
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        total = sum(
            f.stat().st_size
            for f in srv._media_dir.iterdir()
            if f.is_file() and f.suffix.lower() == ".mp4"
        )
        assert total <= srv._quota_bytes, (
            f"Concurrent uploads exceeded quota: {total} bytes > {srv._quota_bytes} bytes quota"
        )
