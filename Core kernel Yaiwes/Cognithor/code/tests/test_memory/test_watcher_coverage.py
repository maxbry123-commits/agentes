"""Coverage-Tests fuer watcher.py -- fehlende Pfade abdecken."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from cognithor.memory.watcher import MemoryFileHandler, MemoryWatcher

if TYPE_CHECKING:
    from pathlib import Path

# ============================================================================
# MemoryFileHandler
# ============================================================================


class TestMemoryFileHandler:
    def test_ignores_non_md(self) -> None:
        callback = MagicMock()
        handler = MemoryFileHandler(callback)
        handler.on_file_changed("test.txt")
        assert handler._pending == {}

    def test_registers_md(self) -> None:
        callback = MagicMock()
        handler = MemoryFileHandler(callback, debounce_seconds=0.0)
        handler.on_file_changed("test.md")
        assert "test.md" in handler._pending

    def test_process_pending_after_debounce(self) -> None:
        callback = MagicMock()
        handler = MemoryFileHandler(callback, debounce_seconds=0.0)
        handler.on_file_changed("test.md")
        # Set time far enough in the past
        handler._pending["test.md"] = time.time() - 10
        processed = handler.process_pending()
        assert "test.md" in processed
        callback.assert_called_once_with("test.md")

    def test_process_pending_not_ready(self) -> None:
        callback = MagicMock()
        handler = MemoryFileHandler(callback, debounce_seconds=999)
        handler.on_file_changed("test.md")
        processed = handler.process_pending()
        assert processed == []

    def test_process_pending_callback_exception(self) -> None:
        callback = MagicMock(side_effect=RuntimeError("fail"))
        handler = MemoryFileHandler(callback, debounce_seconds=0.0)
        handler.on_file_changed("test.md")
        handler._pending["test.md"] = time.time() - 10
        processed = handler.process_pending()
        assert processed == []  # Not added to processed on error


# ============================================================================
# MemoryWatcher
# ============================================================================


class TestMemoryWatcher:
    def test_is_running_default(self, tmp_path: Path) -> None:
        watcher = MemoryWatcher(tmp_path, lambda p: None)
        assert not watcher.is_running

    def test_start_stop_polling(self, tmp_path: Path) -> None:
        tmp_path.mkdir(exist_ok=True)
        callback = MagicMock()
        watcher = MemoryWatcher(tmp_path, callback, poll_interval=0.1)

        with patch.dict(
            "sys.modules", {"watchdog": None, "watchdog.events": None, "watchdog.observers": None}
        ):
            watcher.start()
            assert watcher.is_running
            time.sleep(0.05)
            watcher.stop()
            assert not watcher.is_running

    def test_start_already_running(self, tmp_path: Path) -> None:
        watcher = MemoryWatcher(tmp_path, lambda p: None)
        watcher._running = True
        watcher.start()  # should return immediately

    def test_scan_files(self, tmp_path: Path) -> None:
        (tmp_path / "a.md").write_text("a", encoding="utf-8")
        (tmp_path / "b.txt").write_text("b", encoding="utf-8")

        watcher = MemoryWatcher(tmp_path, lambda p: None)
        watcher._scan_files()
        # Only .md files
        assert str(tmp_path / "a.md") in watcher._file_mtimes

    def test_scan_files_no_dir(self, tmp_path: Path) -> None:
        watcher = MemoryWatcher(tmp_path / "nonexistent", lambda p: None)
        watcher._scan_files()
        assert watcher._file_mtimes == {}

    def test_check_changes_new_file(self, tmp_path: Path) -> None:
        callback = MagicMock()
        watcher = MemoryWatcher(tmp_path, callback, debounce_seconds=0.0)
        watcher._file_mtimes = {}

        (tmp_path / "new.md").write_text("new", encoding="utf-8")
        watcher._check_changes()
        assert str(tmp_path / "new.md") in watcher._handler._pending

    def test_check_changes_modified(self, tmp_path: Path) -> None:
        callback = MagicMock()
        watcher = MemoryWatcher(tmp_path, callback, debounce_seconds=0.0)
        f = tmp_path / "test.md"
        f.write_text("v1", encoding="utf-8")
        watcher._scan_files()
        # Simulate modification
        watcher._file_mtimes[str(f)] = 0
        watcher._check_changes()
        assert str(f) in watcher._handler._pending

    def test_check_changes_no_dir(self, tmp_path: Path) -> None:
        watcher = MemoryWatcher(tmp_path / "nope", lambda p: None)
        watcher._check_changes()  # should not raise

    def test_stop_without_start(self, tmp_path: Path) -> None:
        watcher = MemoryWatcher(tmp_path, lambda p: None)
        watcher.stop()  # should not raise
