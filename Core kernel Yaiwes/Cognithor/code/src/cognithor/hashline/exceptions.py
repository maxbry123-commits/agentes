# Copyright 2024-2026 Cognithor Contributors
# Licensed under the Apache License, Version 2.0
"""Hashline Guard Exceptions."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class HashlineError(Exception):
    """Base exception for all Hashline Guard errors."""

    def __init__(
        self,
        message: str,
        file_path: Path | None = None,
        line_number: int | None = None,
        details: str = "",
    ) -> None:
        super().__init__(message)
        self.file_path = file_path
        self.line_number = line_number
        self.details = details


class HashMismatchError(HashlineError):
    """Raised when a line's hash tag does not match its current content."""

    def __init__(
        self,
        message: str,
        expected_hash: str,
        actual_hash: str,
        line_content: str,
        **kwargs: object,
    ) -> None:
        super().__init__(message, **kwargs)  # type: ignore[arg-type]
        self.expected_hash = expected_hash
        self.actual_hash = actual_hash
        self.line_content = line_content


class StaleReadError(HashlineError):
    """Raised when a cached file read has exceeded the staleness threshold."""

    def __init__(
        self,
        message: str,
        read_timestamp: float,
        age_seconds: float,
        **kwargs: object,
    ) -> None:
        super().__init__(message, **kwargs)  # type: ignore[arg-type]
        self.read_timestamp = read_timestamp
        self.age_seconds = age_seconds


class MaxRetriesExceededError(HashlineError):
    """Raised when an operation has exhausted all retry attempts."""

    def __init__(
        self,
        message: str,
        retry_count: int,
        last_error: str,
        **kwargs: object,
    ) -> None:
        super().__init__(message, **kwargs)  # type: ignore[arg-type]
        self.retry_count = retry_count
        self.last_error = last_error


class BinaryFileError(HashlineError):
    """Raised when a binary file is encountered where a text file is expected."""

    pass


class FileTooLargeError(HashlineError):
    """Raised when a file exceeds the configured maximum size."""

    pass


class CacheFullError(HashlineError):
    """Raised when the cache is full and cannot accept new entries."""

    pass
