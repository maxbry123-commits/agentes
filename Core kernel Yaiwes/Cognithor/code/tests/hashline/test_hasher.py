# Copyright 2024-2026 Cognithor Contributors
# Licensed under the Apache License, Version 2.0
"""Tests for Hashline Guard hasher."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cognithor.hashline.hasher import BASE62_CHARSET, LineHasher

if TYPE_CHECKING:
    from pathlib import Path


class TestHashLineDeterminism:
    """hash_line must produce identical output for identical input."""

    def test_deterministic_100x(self, hasher: LineHasher) -> None:
        content = 'print("hello world")'
        first_tag, first_hash = hasher.hash_line(content)
        for _ in range(99):
            tag, full_hash = hasher.hash_line(content)
            assert tag == first_tag
            assert full_hash == first_hash

    def test_different_content_different_hash(self, hasher: LineHasher) -> None:
        tag1, hash1 = hasher.hash_line("line A")
        tag2, hash2 = hasher.hash_line("line B")
        assert hash1 != hash2


class TestHashLineEdgeCases:
    def test_empty_line(self, hasher: LineHasher) -> None:
        tag, full_hash = hasher.hash_line("")
        assert len(tag) == 2
        assert len(full_hash) == 16
        assert all(c in "0123456789abcdef" for c in full_hash)

    def test_unicode_content(self, hasher: LineHasher) -> None:
        tag, full_hash = hasher.hash_line("hello = 42")
        assert len(tag) == 2
        assert len(full_hash) == 16

    def test_long_line(self, hasher: LineHasher) -> None:
        content = "x" * 50_000
        tag, full_hash = hasher.hash_line(content)
        assert len(tag) == 2
        assert len(full_hash) == 16

    def test_trailing_whitespace_matters(self, hasher: LineHasher) -> None:
        tag1, hash1 = hasher.hash_line("hello")
        tag2, hash2 = hasher.hash_line("hello   ")
        assert hash1 != hash2

    def test_tag_charset(self, hasher: LineHasher) -> None:
        tag, _ = hasher.hash_line("test line")
        assert all(c in BASE62_CHARSET for c in tag)

    def test_full_hash_is_hex(self, hasher: LineHasher) -> None:
        _, full_hash = hasher.hash_line("test")
        assert all(c in "0123456789abcdef" for c in full_hash)


class TestBase62Roundtrip:
    def test_zero(self, hasher: LineHasher) -> None:
        result = hasher._to_base62(0, 2)
        assert result == "00"
        assert len(result) == 2

    def test_small_values(self, hasher: LineHasher) -> None:
        result = hasher._to_base62(61, 2)
        assert len(result) == 2
        assert result[1] == "z"  # 61 = 'z' in base62

    def test_large_value_truncates(self, hasher: LineHasher) -> None:
        # Very large value should still produce exactly 2 chars
        result = hasher._to_base62(999_999_999, 2)
        assert len(result) == 2


class TestHashFile:
    def test_hash_file(self, hasher: LineHasher, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("hello\nworld\n", encoding="utf-8")
        h = hasher.hash_file(f)
        assert len(h) == 64  # SHA-256 hex digest
        # Deterministic
        assert hasher.hash_file(f) == h
