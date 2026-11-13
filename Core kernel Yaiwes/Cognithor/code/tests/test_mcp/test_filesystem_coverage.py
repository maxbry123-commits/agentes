"""Coverage-Tests fuer filesystem.py -- fehlende Pfade abdecken."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from cognithor.mcp.filesystem import (
    FileSystemError,
    FileSystemTools,
    register_fs_tools,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def config(tmp_path: Path) -> MagicMock:
    cfg = MagicMock()
    cfg.security.allowed_paths = [str(tmp_path)]
    cfg.filesystem = None
    return cfg


@pytest.fixture
def fs(config: MagicMock) -> FileSystemTools:
    return FileSystemTools(config)


class TestValidatePath:
    def test_allowed(self, fs: FileSystemTools, tmp_path: Path) -> None:
        path = fs._validate_path(str(tmp_path / "file.txt"))
        assert path.parent == tmp_path

    def test_outside_sandbox(self, fs: FileSystemTools) -> None:
        with pytest.raises(FileSystemError, match="Zugriff verweigert"):
            fs._validate_path("/etc/passwd")

    def test_invalid_path(self, fs: FileSystemTools) -> None:
        # On Windows, null bytes in path may not raise ValueError but
        # the path resolves outside sandbox → "Zugriff verweigert"
        with pytest.raises(FileSystemError):
            fs._validate_path("\x00invalid")


class TestReadFile:
    def test_success(self, fs: FileSystemTools, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("hello world", encoding="utf-8")
        result = fs.read_file(str(f))
        assert "hello world" in result

    def test_not_found(self, fs: FileSystemTools, tmp_path: Path) -> None:
        with pytest.raises(FileSystemError, match="nicht gefunden"):
            fs.read_file(str(tmp_path / "nonexistent.txt"))

    def test_directory(self, fs: FileSystemTools, tmp_path: Path) -> None:
        with pytest.raises(FileSystemError, match="Kein reguläres File"):
            fs.read_file(str(tmp_path))

    def test_line_range(self, fs: FileSystemTools, tmp_path: Path) -> None:
        f = tmp_path / "multi.txt"
        f.write_text("line0\nline1\nline2\nline3", encoding="utf-8")
        result = fs.read_file(str(f), line_start=1, line_end=2)
        assert "line1" in result
        assert "line2" in result

    def test_file_too_large(self, fs: FileSystemTools, tmp_path: Path) -> None:
        f = tmp_path / "big.txt"
        f.write_bytes(b"x" * 2_000_000)
        with pytest.raises(FileSystemError, match="zu groß"):
            fs.read_file(str(f))

    def test_latin1_fallback(self, fs: FileSystemTools, tmp_path: Path) -> None:
        f = tmp_path / "latin.txt"
        f.write_bytes(b"caf\xe9")
        result = fs.read_file(str(f))
        assert "caf" in result


class TestWriteFile:
    def test_success(self, fs: FileSystemTools, tmp_path: Path) -> None:
        f = tmp_path / "output.txt"
        result = fs.write_file(str(f), "hello")
        assert "geschrieben" in result
        assert f.read_text(encoding="utf-8") == "hello"

    def test_creates_parent_dirs(self, fs: FileSystemTools, tmp_path: Path) -> None:
        f = tmp_path / "sub" / "dir" / "file.txt"
        result = fs.write_file(str(f), "nested")
        assert "geschrieben" in result
        assert f.exists()


class TestEditFile:
    def test_success(self, fs: FileSystemTools, tmp_path: Path) -> None:
        f = tmp_path / "edit.txt"
        f.write_text("hello world", encoding="utf-8")
        result = fs.edit_file(str(f), "world", "universe")
        assert "bearbeitet" in result
        assert f.read_text(encoding="utf-8") == "hello universe"

    def test_text_not_found(self, fs: FileSystemTools, tmp_path: Path) -> None:
        f = tmp_path / "edit.txt"
        f.write_text("hello", encoding="utf-8")
        with pytest.raises(FileSystemError, match="nicht gefunden"):
            fs.edit_file(str(f), "missing", "new")

    def test_ambiguous(self, fs: FileSystemTools, tmp_path: Path) -> None:
        f = tmp_path / "edit.txt"
        f.write_text("aa aa", encoding="utf-8")
        with pytest.raises(FileSystemError, match="eindeutig"):
            fs.edit_file(str(f), "aa", "bb")

    def test_old_text_too_large(self, fs: FileSystemTools, tmp_path: Path) -> None:
        f = tmp_path / "edit.txt"
        f.write_text("x", encoding="utf-8")
        with pytest.raises(FileSystemError, match="old_text zu gross"):
            fs.edit_file(str(f), "x" * 600_000, "y")

    def test_new_text_too_large(self, fs: FileSystemTools, tmp_path: Path) -> None:
        f = tmp_path / "edit.txt"
        f.write_text("x", encoding="utf-8")
        with pytest.raises(FileSystemError, match="new_text zu gross"):
            fs.edit_file(str(f), "x", "y" * 600_000)

    def test_file_not_found(self, fs: FileSystemTools, tmp_path: Path) -> None:
        with pytest.raises(FileSystemError, match="nicht gefunden"):
            fs.edit_file(str(tmp_path / "nope.txt"), "a", "b")


class TestListDirectory:
    def test_success(self, fs: FileSystemTools, tmp_path: Path) -> None:
        (tmp_path / "file1.txt").write_text("a", encoding="utf-8")
        sub = tmp_path / "subdir"
        sub.mkdir()
        (sub / "file2.txt").write_text("b", encoding="utf-8")
        result = fs.list_directory(str(tmp_path))
        assert "file1.txt" in result
        assert "subdir" in result

    def test_not_found(self, fs: FileSystemTools, tmp_path: Path) -> None:
        with pytest.raises(FileSystemError, match="nicht gefunden"):
            fs.list_directory(str(tmp_path / "nonexistent"))

    def test_not_a_dir(self, fs: FileSystemTools, tmp_path: Path) -> None:
        f = tmp_path / "file.txt"
        f.write_text("x", encoding="utf-8")
        with pytest.raises(FileSystemError, match="Kein Verzeichnis"):
            fs.list_directory(str(f))

    def test_truncation(self, fs: FileSystemTools, tmp_path: Path) -> None:
        # Create many files to trigger truncation
        fs._max_tree_entries = 5
        for i in range(20):
            (tmp_path / f"file{i:03d}.txt").write_text("x", encoding="utf-8")
        result = fs.list_directory(str(tmp_path))
        assert "weitere" in result


class TestFormatSize:
    def test_bytes(self) -> None:
        assert "B" in FileSystemTools._format_size(100)

    def test_kilobytes(self) -> None:
        assert "KB" in FileSystemTools._format_size(2048)

    def test_megabytes(self) -> None:
        assert "MB" in FileSystemTools._format_size(2_000_000)


class TestRegisterFsTools:
    def test_registers_five_tools(self, config: MagicMock) -> None:
        mock_client = MagicMock()
        fs = register_fs_tools(mock_client, config)
        assert isinstance(fs, FileSystemTools)
        # 4 real tools + 1 alias (file_write -> write_file) for LLM compat
        assert mock_client.register_builtin_handler.call_count == 5
        names = [call.args[0] for call in mock_client.register_builtin_handler.call_args_list]
        assert "read_file" in names
        assert "write_file" in names
        assert "file_write" in names  # alias
        assert "edit_file" in names
        assert "list_directory" in names
