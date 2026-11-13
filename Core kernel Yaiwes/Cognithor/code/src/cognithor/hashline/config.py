# Copyright 2024-2026 Cognithor Contributors
# Licensed under the Apache License, Version 2.0
"""Hashline Guard configuration."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from cognithor.utils.logging import get_logger

if TYPE_CHECKING:
    from pathlib import Path

log = get_logger(__name__)


@dataclass
class HashlineConfig:
    """Configuration for the Hashline Guard system.

    Attributes:
        enabled: Whether hashline guard is active.
        hash_algorithm: Algorithm for line hashing (default: xxhash64).
        tag_length: Length of the short base62 tag (default: 2).
        tag_charset: Character set for base62 encoding.
        max_file_size_mb: Maximum file size in megabytes.
        max_line_length: Maximum line length in characters.
        stale_threshold_seconds: Seconds before a cached read is considered stale.
        max_retries: Maximum number of retries for hash-verified edits.
        retry_delay_seconds: Delay between retries in seconds.
        cache_max_files: Maximum number of files to keep in the LRU cache.
        binary_detection: Whether to detect and reject binary files.
        audit_enabled: Whether to log edit operations for audit.
        excluded_patterns: Glob patterns for files to exclude from hashing.
        protected_paths: Paths that require extra confirmation before editing.
    """

    enabled: bool = True
    hash_algorithm: str = "xxhash64"
    tag_length: int = 2
    tag_charset: str = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    max_file_size_mb: float = 10.0
    max_line_length: int = 10_000
    stale_threshold_seconds: float = 30.0
    max_retries: int = 3
    retry_delay_seconds: float = 0.5
    cache_max_files: int = 100
    binary_detection: bool = True
    audit_enabled: bool = True
    excluded_patterns: list[str] = field(
        default_factory=lambda: [
            "*.pyc",
            "*.pyo",
            "__pycache__/*",
            ".git/*",
            "node_modules/*",
            "*.min.js",
            "*.min.css",
        ]
    )
    protected_paths: list[str] = field(
        default_factory=lambda: [
            "*.env",
            "*.pem",
            "*.key",
            "*credentials*",
            "*secret*",
        ]
    )

    @classmethod
    def from_dict(cls, d: dict[str, object]) -> HashlineConfig:
        """Create a config from a dictionary, ignoring unknown keys.

        Args:
            d: Dictionary of configuration values.

        Returns:
            A new HashlineConfig instance.
        """
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in known_fields}
        return cls(**filtered)  # type: ignore[arg-type]

    @classmethod
    def default(cls) -> HashlineConfig:
        """Return the default configuration.

        Returns:
            A HashlineConfig with all default values.
        """
        return cls()

    def is_excluded(self, path: Path) -> bool:
        """Check if a path matches any exclusion pattern.

        Args:
            path: The file path to check.

        Returns:
            True if the path should be excluded from hashing.
        """
        path_str = str(path)
        for pattern in self.excluded_patterns:
            if fnmatch.fnmatch(path_str, pattern):
                return True
            # Also match against just the filename
            if fnmatch.fnmatch(path.name, pattern):
                return True
        return False

    def is_protected(self, path: Path) -> bool:
        """Check if a path matches any protected pattern.

        Args:
            path: The file path to check.

        Returns:
            True if the path is protected and requires extra confirmation.
        """
        path_str = str(path)
        for pattern in self.protected_paths:
            if fnmatch.fnmatch(path_str, pattern):
                return True
            if fnmatch.fnmatch(path.name, pattern):
                return True
        return False
