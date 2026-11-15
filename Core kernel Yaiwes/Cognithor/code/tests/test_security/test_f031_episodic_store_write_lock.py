"""Tests fuer F-031: EpisodicStore SQLite ohne Application-Level Locking.

Prueft dass:
  - _write_lock als threading.RLock existiert
  - store_episode unter dem Lock ausfuehrt
  - store_summary unter dem Lock ausfuehrt
  - _ensure_schema unter dem Lock ausfuehrt
  - Concurrent Writes nicht zu "database is locked" fuehren
  - Read-Operationen ohne Lock funktionieren
  - Source-Code das Lock-Pattern enthaelt
"""

from __future__ import annotations

import inspect
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING

from cognithor.memory.episodic_store import EpisodicStore

if TYPE_CHECKING:
    from pathlib import Path

# ============================================================================
# Write-Lock existiert
# ============================================================================


class TestWriteLockExists:
    """Prueft dass _write_lock korrekt initialisiert wird."""

    def test_write_lock_attribute(self) -> None:
        store = EpisodicStore()
        assert hasattr(store, "_write_lock")

    def test_write_lock_is_rlock(self) -> None:
        store = EpisodicStore()
        assert isinstance(store._write_lock, type(threading.RLock()))

    def test_write_lock_is_reentrant(self) -> None:
        """RLock erlaubt mehrfaches Acquiren im selben Thread."""
        store = EpisodicStore()
        with store._write_lock, store._write_lock:
            pass  # Kein Deadlock


# ============================================================================
# Write-Operationen unter Lock
# ============================================================================


class _TrackingRLock:
    """RLock-Wrapper der acquire/release-Aufrufe zaehlt."""

    def __init__(self) -> None:
        self._real = threading.RLock()
        self.acquire_count = 0

    def acquire(self, *args, **kwargs):
        self.acquire_count += 1
        return self._real.acquire(*args, **kwargs)

    def release(self):
        return self._real.release()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *exc):
        self.release()


class TestWriteOperationsLocked:
    """Prueft dass Write-Operationen unter dem Lock laufen."""

    def test_store_episode_acquires_lock(self) -> None:
        """store_episode() verwendet _write_lock."""
        store = EpisodicStore()
        tracker = _TrackingRLock()
        store._write_lock = tracker
        store.store_episode("s1", "topic", "content")
        assert tracker.acquire_count >= 1

    def test_store_summary_acquires_lock(self) -> None:
        """store_summary() verwendet _write_lock."""
        store = EpisodicStore()
        tracker = _TrackingRLock()
        store._write_lock = tracker
        store.store_summary("daily", "2026-01-01", "2026-01-02", "summary")
        assert tracker.acquire_count >= 1


# ============================================================================
# Concurrent Writes
# ============================================================================


class TestConcurrentWrites:
    """Prueft dass parallele Writes sicher sind."""

    def test_concurrent_store_episodes(self, tmp_path: Path) -> None:
        """Parallele store_episode Aufrufe fuehren nicht zu Fehlern."""
        store = EpisodicStore(db_path=tmp_path / "test.db")
        errors: list[str] = []

        def write_episode(i: int) -> str:
            try:
                return store.store_episode(
                    session_id=f"session-{i}",
                    topic=f"topic-{i}",
                    content=f"content for episode {i}",
                    success_score=float(i) / 100,
                )
            except Exception as e:
                errors.append(str(e))
                return ""

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(write_episode, i) for i in range(50)]
            [f.result() for f in as_completed(futures)]

        assert len(errors) == 0, f"Errors: {errors}"
        assert store.get_episode_count() == 50

    def test_concurrent_store_summaries(self, tmp_path: Path) -> None:
        """Parallele store_summary Aufrufe fuehren nicht zu Fehlern."""
        store = EpisodicStore(db_path=tmp_path / "test.db")
        errors: list[str] = []

        def write_summary(i: int) -> str:
            try:
                return store.store_summary(
                    period="daily",
                    start_date=f"2026-01-{i + 1:02d}",
                    end_date=f"2026-01-{i + 1:02d}",
                    summary=f"Summary {i}",
                )
            except Exception as e:
                errors.append(str(e))
                return ""

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(write_summary, i) for i in range(30)]
            [f.result() for f in as_completed(futures)]

        assert len(errors) == 0, f"Errors: {errors}"
        summaries = store.get_summaries()
        assert len(summaries) == 30

    def test_mixed_reads_and_writes(self, tmp_path: Path) -> None:
        """Gleichzeitige Reads und Writes funktionieren."""
        store = EpisodicStore(db_path=tmp_path / "test.db")
        # Pre-populate
        for i in range(10):
            store.store_episode(f"s{i}", f"topic-{i}", f"content-{i}")

        errors: list[str] = []

        def writer(i: int) -> None:
            try:
                store.store_episode(f"sw{i}", f"write-topic-{i}", f"write-content-{i}")
            except Exception as e:
                errors.append(f"write: {e}")

        def reader(i: int) -> None:
            try:
                store.get_episode_count()
                store.get_session_episodes(f"s{i % 10}")
            except Exception as e:
                errors.append(f"read: {e}")

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = []
            for i in range(20):
                futures.append(pool.submit(writer, i))
                futures.append(pool.submit(reader, i))
            for f in as_completed(futures):
                f.result()

        assert len(errors) == 0, f"Errors: {errors}"


# ============================================================================
# Read-Operationen
# ============================================================================


class TestReadOperations:
    """Prueft dass Read-Operationen weiterhin funktionieren."""

    def test_search_after_store(self) -> None:
        store = EpisodicStore()
        store.store_episode("s1", "Python programming", "Learned about decorators")
        results = store.search_episodes("Python")
        assert len(results) >= 1

    def test_get_session_episodes(self) -> None:
        store = EpisodicStore()
        store.store_episode("session-abc", "topic", "content")
        episodes = store.get_session_episodes("session-abc")
        assert len(episodes) == 1

    def test_get_episode_count(self) -> None:
        store = EpisodicStore()
        assert store.get_episode_count() == 0
        store.store_episode("s1", "t", "c")
        assert store.get_episode_count() == 1


# ============================================================================
# Source-Level-Checks
# ============================================================================


class TestSourceLevelChecks:
    """Prueft den Source-Code auf den Fix."""

    def test_threading_imported(self) -> None:
        import cognithor.memory.episodic_store as mod

        source = inspect.getsource(mod)
        assert "import threading" in source

    def test_write_lock_in_init(self) -> None:
        source = inspect.getsource(EpisodicStore.__init__)
        assert "_write_lock" in source
        assert "RLock" in source

    def test_write_lock_in_store_episode(self) -> None:
        source = inspect.getsource(EpisodicStore.store_episode)
        assert "_write_lock" in source

    def test_write_lock_in_store_summary(self) -> None:
        source = inspect.getsource(EpisodicStore.store_summary)
        assert "_write_lock" in source

    def test_write_lock_in_ensure_schema(self) -> None:
        source = inspect.getsource(EpisodicStore._ensure_schema)
        assert "_write_lock" in source
