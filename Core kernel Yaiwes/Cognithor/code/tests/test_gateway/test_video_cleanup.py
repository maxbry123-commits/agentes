from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path

import pytest

from cognithor.gateway.video_cleanup import VideoCleanupWorker


def _touch(path: Path, size: int = 64, mtime_age_sec: float = 0.0) -> None:
    """Create a file with optional artificially-old mtime."""
    path.write_bytes(b"x" * size)
    if mtime_age_sec > 0:
        t = time.time() - mtime_age_sec
        os.utime(path, (t, t))


class TestRegisterAndSessionClose:
    @pytest.mark.asyncio
    async def test_register_upload_is_tracked_by_session(self, tmp_path: Path):
        worker = VideoCleanupWorker(media_dir=tmp_path, ttl_hours=24)
        worker.register_upload("abc123", "session-1")
        worker.register_upload("def456", "session-1")
        worker.register_upload("ghi789", "session-2")
        assert set(worker._by_session["session-1"]) == {"abc123", "def456"}
        assert worker._by_session["session-2"] == ["ghi789"]

    @pytest.mark.asyncio
    async def test_on_session_close_deletes_only_that_sessions_files(self, tmp_path: Path):
        _touch(tmp_path / "abc123.mp4")
        _touch(tmp_path / "abc123.jpg")  # thumbnail sidecar
        _touch(tmp_path / "def456.mp4")
        _touch(tmp_path / "ghi789.mp4")

        worker = VideoCleanupWorker(media_dir=tmp_path, ttl_hours=24)
        worker.register_upload("abc123", "session-1")
        worker.register_upload("def456", "session-1")
        worker.register_upload("ghi789", "session-2")

        await worker.on_session_close("session-1")

        assert not (tmp_path / "abc123.mp4").exists()
        assert not (tmp_path / "abc123.jpg").exists()
        assert not (tmp_path / "def456.mp4").exists()
        assert (tmp_path / "ghi789.mp4").exists()
        assert "session-1" not in worker._by_session

    @pytest.mark.asyncio
    async def test_on_session_close_for_unknown_session_is_noop(self, tmp_path: Path):
        worker = VideoCleanupWorker(media_dir=tmp_path, ttl_hours=24)
        await worker.on_session_close("ghost-session")


class TestTTLSweep:
    @pytest.mark.asyncio
    async def test_sweep_deletes_files_older_than_ttl(self, tmp_path: Path):
        old = tmp_path / "old-uuid.mp4"
        fresh = tmp_path / "fresh-uuid.mp4"
        _touch(old, mtime_age_sec=25 * 3600)  # 25 h old
        _touch(fresh, mtime_age_sec=1 * 3600)  # 1 h old

        worker = VideoCleanupWorker(media_dir=tmp_path, ttl_hours=24)
        await worker._sweep_once()

        assert not old.exists()
        assert fresh.exists()

    @pytest.mark.asyncio
    async def test_sweep_deletes_thumbnails_too(self, tmp_path: Path):
        old_video = tmp_path / "old.mp4"
        old_thumb = tmp_path / "old.jpg"
        _touch(old_video, mtime_age_sec=25 * 3600)
        _touch(old_thumb, mtime_age_sec=25 * 3600)

        worker = VideoCleanupWorker(media_dir=tmp_path, ttl_hours=24)
        await worker._sweep_once()

        assert not old_video.exists()
        assert not old_thumb.exists()

    @pytest.mark.asyncio
    async def test_sweep_ignores_missing_dir(self, tmp_path: Path):
        missing = tmp_path / "does-not-exist"
        worker = VideoCleanupWorker(media_dir=missing, ttl_hours=24)
        # Must not raise
        await worker._sweep_once()


class TestStartStop:
    @pytest.mark.asyncio
    async def test_start_runs_initial_sweep(self, tmp_path: Path):
        old = tmp_path / "old.mp4"
        _touch(old, mtime_age_sec=25 * 3600)

        worker = VideoCleanupWorker(media_dir=tmp_path, ttl_hours=24, sweep_interval_sec=0.05)
        await worker.start()
        await asyncio.sleep(0.02)  # give the initial sweep a moment
        await worker.stop()

        assert not old.exists()

    @pytest.mark.asyncio
    async def test_stop_is_idempotent(self, tmp_path: Path):
        worker = VideoCleanupWorker(media_dir=tmp_path, ttl_hours=24)
        await worker.start()
        await worker.stop()
        await worker.stop()  # second stop must not raise


class TestStartIdempotent:
    @pytest.mark.asyncio
    async def test_double_start_does_not_leak_second_task(self, tmp_path: Path):
        """Regression for Bug C2-r3: start() called twice must not orphan the
        first sweep task. Without the idempotency guard, the first _sweep_task
        reference is overwritten and the task runs forever."""
        worker = VideoCleanupWorker(media_dir=tmp_path, ttl_hours=24, sweep_interval_sec=0.05)
        await worker.start()
        first_task = worker._sweep_task
        assert first_task is not None

        # Second start() must either return the same task or leave the first one
        # intact and not running in parallel with a second one.
        await worker.start()
        second_task = worker._sweep_task

        # Either the same task object OR the first task has been cleanly
        # cancelled/replaced. The concrete invariant: no more than ONE active
        # sweep task exists.
        assert first_task is second_task or first_task.done(), (
            "Second start() orphaned the first sweep task: "
            f"first_task.done={first_task.done()}, different-object={first_task is not second_task}"
        )

        await worker.stop()
