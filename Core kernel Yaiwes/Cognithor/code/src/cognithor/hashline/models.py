# Copyright 2024-2026 Cognithor Contributors
# Licensed under the Apache License, Version 2.0
"""Hashline Guard data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class HashlinedLine:
    """A single line with its hash tag and metadata.

    Attributes:
        number: 1-based line number.
        content: The raw line content (without newline).
        hash_tag: Short 2-character base62 tag.
        full_hash: Full 16-character hex hash for verification.
    """

    number: int
    content: str
    hash_tag: str
    full_hash: str


@dataclass
class HashlinedFile:
    """A file whose lines have been hashed.

    Attributes:
        path: Resolved absolute path to the file.
        lines: List of hashlined lines.
        file_hash: SHA-256 hash of the entire file.
        read_timestamp: Unix timestamp when the file was read.
        encoding: Encoding used to read the file.
    """

    path: Path
    lines: list[HashlinedLine]
    file_hash: str
    read_timestamp: float
    encoding: str


@dataclass
class EditIntent:
    """Describes an intended edit operation parsed from an LLM command.

    Attributes:
        file_path: Path to the file to edit.
        target_line: 1-based line number to operate on.
        target_hash: Expected 2-char hash tag for verification.
        operation: One of "replace", "insert_after", "insert_before", "delete".
        new_content: New content for replace/insert operations (None for delete).
        context_lines: Number of context lines to include in output.
    """

    file_path: Path
    target_line: int
    target_hash: str
    operation: str  # "replace", "insert_after", "insert_before", "delete"
    new_content: str | None
    context_lines: int = 3


@dataclass
class EditResult:
    """Result of an edit operation.

    Attributes:
        success: Whether the edit succeeded.
        operation: The operation that was performed.
        file_path: Path to the edited file.
        line_number: Line number that was edited.
        old_content: Previous content of the line (None for insert).
        new_content: New content of the line (None for delete).
        audit_hash: Hash for audit trail.
        error: Error message if the edit failed.
        retry_count: Number of retries that were needed.
    """

    success: bool
    operation: str
    file_path: Path
    line_number: int
    old_content: str | None
    new_content: str | None
    audit_hash: str
    error: str | None = None
    retry_count: int = 0


@dataclass
class CacheStats:
    """Statistics for the hashline cache.

    Attributes:
        hits: Number of cache hits.
        misses: Number of cache misses.
        evictions: Number of LRU evictions.
        size: Current number of entries in the cache.
    """

    hits: int = field(default=0)
    misses: int = field(default=0)
    evictions: int = field(default=0)
    size: int = field(default=0)
