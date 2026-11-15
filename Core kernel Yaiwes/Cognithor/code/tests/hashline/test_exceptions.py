# Copyright 2024-2026 Cognithor Contributors
# Licensed under the Apache License, Version 2.0
"""Tests for Hashline Guard exceptions."""

from __future__ import annotations

from pathlib import Path

from cognithor.hashline.exceptions import (
    BinaryFileError,
    CacheFullError,
    FileTooLargeError,
    HashlineError,
    HashMismatchError,
    MaxRetriesExceededError,
    StaleReadError,
)


class TestHashlineError:
    def test_base_error_attributes(self) -> None:
        path = Path("/tmp/test.py")
        err = HashlineError("something broke", file_path=path, line_number=42, details="extra info")
        assert str(err) == "something broke"
        assert err.file_path == path
        assert err.line_number == 42
        assert err.details == "extra info"

    def test_base_error_defaults(self) -> None:
        err = HashlineError("msg")
        assert err.file_path is None
        assert err.line_number is None
        assert err.details == ""


class TestHashMismatchError:
    def test_attributes(self) -> None:
        err = HashMismatchError(
            "mismatch",
            expected_hash="AB",
            actual_hash="CD",
            line_content="hello",
            file_path=Path("/tmp/f.py"),
            line_number=10,
        )
        assert err.expected_hash == "AB"
        assert err.actual_hash == "CD"
        assert err.line_content == "hello"
        assert err.file_path == Path("/tmp/f.py")
        assert isinstance(err, HashlineError)


class TestStaleReadError:
    def test_attributes(self) -> None:
        err = StaleReadError("stale", read_timestamp=1000.0, age_seconds=60.0)
        assert err.read_timestamp == 1000.0
        assert err.age_seconds == 60.0
        assert isinstance(err, HashlineError)


class TestMaxRetriesExceededError:
    def test_attributes(self) -> None:
        err = MaxRetriesExceededError("retries", retry_count=3, last_error="timeout")
        assert err.retry_count == 3
        assert err.last_error == "timeout"
        assert isinstance(err, HashlineError)


class TestSimpleErrors:
    def test_binary_file_error(self) -> None:
        err = BinaryFileError("binary", file_path=Path("/tmp/img.bin"))
        assert isinstance(err, HashlineError)
        assert err.file_path == Path("/tmp/img.bin")

    def test_file_too_large_error(self) -> None:
        err = FileTooLargeError("too large")
        assert isinstance(err, HashlineError)

    def test_cache_full_error(self) -> None:
        err = CacheFullError("full")
        assert isinstance(err, HashlineError)
