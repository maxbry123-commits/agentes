# Copyright 2024-2026 Cognithor Contributors
# Licensed under the Apache License, Version 2.0
"""Datei-Leser mit Hashline-Tagging."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from cognithor.hashline.exceptions import BinaryFileError, FileTooLargeError
from cognithor.hashline.models import HashlinedFile, HashlinedLine
from cognithor.utils.logging import get_logger

if TYPE_CHECKING:
    from pathlib import Path

    from cognithor.hashline.cache import HashlineCache
    from cognithor.hashline.config import HashlineConfig
    from cognithor.hashline.hasher import LineHasher

log = get_logger(__name__)

_BINARY_CHECK_SIZE = 8192


class HashlineTagger:
    """Reads files and produces hashlined output with per-line tags.

    Args:
        hasher: LineHasher for computing per-line hashes.
        cache: HashlineCache for storing/retrieving tagged files.
        config: HashlineConfig for size limits and binary detection.
    """

    def __init__(
        self,
        hasher: LineHasher,
        cache: HashlineCache,
        config: HashlineConfig,
    ) -> None:
        self._hasher = hasher
        self._cache = cache
        self._config = config

    def read_and_tag(self, path: Path) -> HashlinedFile:
        """Read a file, hash every line, cache the result, and return it.

        Args:
            path: Path to the file to read.

        Returns:
            HashlinedFile with all lines tagged.

        Raises:
            FileNotFoundError: If the file does not exist.
            BinaryFileError: If the file appears to be binary.
            FileTooLargeError: If the file exceeds the configured size limit.
        """
        resolved = path.resolve()

        if not resolved.exists():
            raise FileNotFoundError(f"File not found: {resolved}")

        # Size check
        size_bytes = resolved.stat().st_size
        max_bytes = int(self._config.max_file_size_mb * 1024 * 1024)
        if size_bytes > max_bytes:
            raise FileTooLargeError(
                f"File too large: {size_bytes:,} bytes (max {self._config.max_file_size_mb} MB)",
                file_path=resolved,
            )

        # Binary detection
        if self._config.binary_detection and self.is_binary(resolved):
            raise BinaryFileError(
                f"Binary file detected: {resolved}",
                file_path=resolved,
            )

        # Encoding detection: try utf-8, then latin-1, then errors="replace"
        content, encoding = self._read_with_encoding(resolved)

        # Split into lines (preserving the fact that last line may lack newline)
        raw_lines = content.split("\n")
        # If the content ends with a newline, split produces an extra empty string
        # but we keep it because it represents a real empty last line in most editors.
        # However, if the file is empty, we get [''] which is 1 line.

        lines: list[HashlinedLine] = []
        for i, line_content in enumerate(raw_lines, start=1):
            tag, full_hash = self._hasher.hash_line(line_content)
            lines.append(
                HashlinedLine(
                    number=i,
                    content=line_content,
                    hash_tag=tag,
                    full_hash=full_hash,
                )
            )

        file_hash = self._hasher.hash_file(resolved)
        result = HashlinedFile(
            path=resolved,
            lines=lines,
            file_hash=file_hash,
            read_timestamp=time.time(),
            encoding=encoding,
        )

        self._cache.put(resolved, result)
        log.debug("file_tagged", path=str(resolved), lines=len(lines), encoding=encoding)
        return result

    def read_range(self, path: Path, start: int, end: int) -> HashlinedFile:
        """Read and tag only a specific range of lines (1-based, inclusive).

        Args:
            path: Path to the file.
            start: First line number (1-based, inclusive).
            end: Last line number (1-based, inclusive).

        Returns:
            HashlinedFile containing only the requested lines.
        """
        full = self.read_and_tag(path)
        selected = [line for line in full.lines if start <= line.number <= end]
        return HashlinedFile(
            path=full.path,
            lines=selected,
            file_hash=full.file_hash,
            read_timestamp=full.read_timestamp,
            encoding=full.encoding,
        )

    def is_binary(self, path: Path) -> bool:
        """Check if a file appears to be binary by looking for NULL bytes.

        Args:
            path: Path to the file to check.

        Returns:
            True if the file contains NULL bytes in its first 8192 bytes.
        """
        try:
            with open(path, "rb") as f:
                chunk = f.read(_BINARY_CHECK_SIZE)
            return b"\x00" in chunk
        except OSError:
            return False

    @staticmethod
    def _read_with_encoding(path: Path) -> tuple[str, str]:
        """Try to read a file with multiple encodings.

        Returns:
            Tuple of (content, encoding_used).
        """
        # Try UTF-8 first
        try:
            content = path.read_text(encoding="utf-8")
            return content, "utf-8"
        except UnicodeDecodeError:
            pass

        # Try Latin-1
        try:
            content = path.read_text(encoding="latin-1")
            return content, "latin-1"
        except UnicodeDecodeError:
            pass

        # Fallback with replacement
        content = path.read_text(encoding="utf-8", errors="replace")
        return content, "utf-8-replace"
