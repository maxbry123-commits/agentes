"""VideoCleanupWorker — deletes uploaded videos on session close + TTL expiry.

No persistent state — the 24 h filesystem-mtime-based TTL sweep is authoritative.
Session tracking is an optimization: users who close a session before the TTL
window get their videos deleted sooner. If Cognithor crashes mid-session and
never fires ``on_session_close``, the TTL sweep picks up the orphans on the next
run or within the hour.

See spec: docs/superpowers/specs/2026-04-23-video-input-vllm-design.md
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

from cognithor.utils.logging import get_logger

log = get_logger(__name__)


class VideoCleanupWorker:
    """Manages per-session cleanup and a periodic TTL sweep."""

    def __init__(
        self,
        media_dir: Path,
        *,
        ttl_hours: int = 24,
        sweep_interval_sec: float = 60.0,
    ) -> None:
        self._media_dir = Path(media_dir)
        self._ttl_hours = ttl_hours
        self._sweep_interval = sweep_interval_sec
        self._by_session: dict[str, list[str]] = {}
        self._sweep_task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        """Run TTL sweep once at start, then kick off the periodic sweep loop.

        Idempotent: if a sweep task is already running, skip the restart so
        retry paths (e.g. after a partial media-server bind failure) don't
        orphan the first task. A previous task that has already finished is
        cleared before a fresh one is scheduled.
        """
        if self._sweep_task is not None and not self._sweep_task.done():
            log.debug("video_cleanup_already_started")
            return
        # If there's a previous finished task, clear it before creating a new one.
        self._sweep_task = None
        await self._sweep_once()
        self._stop_event.clear()
        self._sweep_task = asyncio.create_task(self._run_periodic())
        log.info("video_cleanup_started", media_dir=str(self._media_dir), ttl_hours=self._ttl_hours)

    async def stop(self) -> None:
        """Cancel the periodic sweep. Idempotent."""
        if self._sweep_task is None:
            return
        self._stop_event.set()
        try:
            await asyncio.wait_for(self._sweep_task, timeout=2.0)
        except (TimeoutError, asyncio.CancelledError):
            self._sweep_task.cancel()
        self._sweep_task = None
        log.info("video_cleanup_stopped")

    def register_upload(self, uuid: str, session_id: str) -> None:
        """Track this upload so it's deleted when the session closes."""
        self._by_session.setdefault(session_id, []).append(uuid)

    async def on_session_close(self, session_id: str) -> None:
        """Delete all uploads (and thumbnails) registered under this session."""
        uuids = self._by_session.pop(session_id, [])
        for uuid in uuids:
            self._delete_upload(uuid)

    def _delete_upload(self, uuid: str) -> None:
        """Remove any file starting with ``<uuid>.`` in the media dir."""
        if not self._media_dir.is_dir():
            return
        for path in self._media_dir.glob(f"{uuid}.*"):
            try:
                path.unlink()
            except OSError as exc:
                log.warning(
                    "video_cleanup_delete_failed",
                    uuid=uuid,
                    path=str(path),
                    error=str(exc),
                )

    async def _run_periodic(self) -> None:
        """Loop: wait ``_sweep_interval`` seconds, sweep, repeat until stopped."""
        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self._sweep_interval)
                return  # stop signal arrived
            except TimeoutError:
                pass
            await self._sweep_once()

    async def _sweep_once(self) -> None:
        """Delete every file in ``media_dir`` whose mtime is older than ttl_hours."""
        if not self._media_dir.is_dir():
            return
        cutoff = time.time() - self._ttl_hours * 3600
        deleted = 0
        for path in self._media_dir.iterdir():
            if not path.is_file():
                continue
            try:
                if path.stat().st_mtime < cutoff:
                    path.unlink()
                    deleted += 1
            except OSError as exc:
                log.warning("video_ttl_sweep_failed", path=str(path), error=str(exc))
        if deleted:
            log.info("video_ttl_sweep_completed", deleted=deleted)
