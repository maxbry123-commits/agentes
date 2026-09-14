# Copyright 2024-2026 Cognithor Contributors
# Licensed under the Apache License, Version 2.0
"""Hashline Guard — deterministic line hashing."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

import xxhash

from cognithor.hashline.config import HashlineConfig
from cognithor.utils.logging import get_logger

if TYPE_CHECKING:
    from pathlib import Path

log = get_logger(__name__)

BASE62_CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


class LineHasher:
    """Deterministic line-level hasher using xxhash64.

    Produces a short base62 tag (2 chars) and a full 16-char hex digest
    for each line. Trailing whitespace IS included in the hash.

    Args:
        config: Hashline configuration. Uses defaults if not provided.
    """

    def __init__(self, config: HashlineConfig | None = None) -> None:
        self._config = config or HashlineConfig.default()
        self._charset = self._config.tag_charset
        self._tag_length = self._config.tag_length

    def hash_line(self, content: str) -> tuple[str, str]:
        """Hash a single line's content.

        Args:
            content: The line content to hash. Trailing whitespace is included.

        Returns:
            A tuple of (tag, full_hash) where tag is a 2-char base62 string
            and full_hash is the 16-char hex digest.
        """
        digest = xxhash.xxh64(content.encode("utf-8"))
        full_hash = digest.hexdigest()
        int_value = digest.intdigest()
        tag = self._to_base62(int_value, self._tag_length)
        return tag, full_hash

    def hash_file(self, path: Path, encoding: str = "utf-8") -> str:
        """Compute SHA-256 hash of an entire file.

        Args:
            path: Path to the file.
            encoding: File encoding (unused for binary hash, but kept for API
                consistency).

        Returns:
            Hex-encoded SHA-256 digest of the file contents.
        """
        sha = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                sha.update(chunk)
        return sha.hexdigest()

    def _to_base62(self, value: int, length: int) -> str:
        """Convert an integer to a fixed-length base62 string.

        Args:
            value: Non-negative integer to convert.
            length: Desired output length (zero-padded).

        Returns:
            A base62-encoded string of exactly ``length`` characters.
        """
        base = len(self._charset)
        chars: list[str] = []
        remaining = value
        for _ in range(length):
            chars.append(self._charset[remaining % base])
            remaining //= base
        # Reverse so most-significant digit is first
        chars.reverse()
        return "".join(chars)
