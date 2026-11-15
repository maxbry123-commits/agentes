# Copyright 2024-2026 Cognithor Contributors
# Licensed under the Apache License, Version 2.0
"""Tests for HashlineTagger."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from cognithor.hashline.cache import HashlineCache
from cognithor.hashline.config import HashlineConfig
from cognithor.hashline.exceptions import BinaryFileError, FileTooLargeError
from cognithor.hashline.hasher import LineHasher
from cognithor.hashline.tagger import HashlineTagger

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def tagger(config: HashlineConfig, hasher: LineHasher, cache: HashlineCache) -> HashlineTagger:
    return HashlineTagger(hasher, cache, config)


class TestReadAndTag:
    def test_utf8_file(self, tagger: HashlineTagger, tmp_path: Path) -> None:
        p = tmp_path / "utf8.py"
        p.write_text("hello\nworld", encoding="utf-8")
        result = tagger.read_and_tag(p)
        assert len(result.lines) == 2
        assert result.lines[0].content == "hello"
        assert result.lines[1].content == "world"
        assert result.encoding == "utf-8"

    def test_latin1_file(self, tagger: HashlineTagger, tmp_path: Path) -> None:
        p = tmp_path / "latin1.txt"
        p.write_bytes("caf\xe9\nna\xefve".encode("latin-1"))
        result = tagger.read_and_tag(p)
        assert len(result.lines) == 2
        assert result.encoding == "latin-1"

    def test_binary_detection(self, tagger: HashlineTagger, tmp_path: Path) -> None:
        p = tmp_path / "binary.bin"
        p.write_bytes(b"\x00\x01\x02\x03" * 100)
        with pytest.raises(BinaryFileError):
            tagger.read_and_tag(p)

    def test_binary_detection_disabled(self, tmp_path: Path) -> None:
        cfg = HashlineConfig(binary_detection=False)
        hasher = LineHasher(cfg)
        cache = HashlineCache(cfg)
        t = HashlineTagger(hasher, cache, cfg)
        p = tmp_path / "binary.bin"
        p.write_bytes(b"\x00\x01\x02\x03")
        # Should not raise
        result = t.read_and_tag(p)
        assert len(result.lines) >= 1

    def test_file_too_large(self, tmp_path: Path) -> None:
        cfg = HashlineConfig(max_file_size_mb=0.001)  # ~1KB
        hasher = LineHasher(cfg)
        cache = HashlineCache(cfg)
        t = HashlineTagger(hasher, cache, cfg)
        p = tmp_path / "big.txt"
        p.write_text("x" * 2000, encoding="utf-8")
        with pytest.raises(FileTooLargeError):
            t.read_and_tag(p)

    def test_empty_file(self, tagger: HashlineTagger, tmp_path: Path) -> None:
        p = tmp_path / "empty.txt"
        p.write_text("", encoding="utf-8")
        result = tagger.read_and_tag(p)
        # Empty file has 1 line (the empty string after split)
        assert len(result.lines) == 1
        assert result.lines[0].content == ""

    def test_no_trailing_newline(self, tagger: HashlineTagger, tmp_path: Path) -> None:
        p = tmp_path / "no_nl.txt"
        p.write_text("line1\nline2", encoding="utf-8")
        result = tagger.read_and_tag(p)
        assert len(result.lines) == 2
        assert result.lines[1].content == "line2"

    def test_trailing_newline(self, tagger: HashlineTagger, tmp_path: Path) -> None:
        p = tmp_path / "with_nl.txt"
        p.write_text("line1\nline2\n", encoding="utf-8")
        result = tagger.read_and_tag(p)
        assert len(result.lines) == 3
        assert result.lines[2].content == ""

    def test_crlf_file(self, tagger: HashlineTagger, tmp_path: Path) -> None:
        p = tmp_path / "crlf.txt"
        p.write_bytes(b"line1\r\nline2\r\nline3")
        result = tagger.read_and_tag(p)
        # split("\n") will leave \r on lines in CRLF files
        assert len(result.lines) >= 2

    def test_file_not_found(self, tagger: HashlineTagger, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            tagger.read_and_tag(tmp_path / "nope.txt")

    def test_lines_are_one_based(self, tagger: HashlineTagger, tmp_path: Path) -> None:
        p = tmp_path / "numbered.txt"
        p.write_text("a\nb\nc", encoding="utf-8")
        result = tagger.read_and_tag(p)
        assert result.lines[0].number == 1
        assert result.lines[1].number == 2
        assert result.lines[2].number == 3


class TestReadRange:
    def test_basic_range(self, tagger: HashlineTagger, tmp_path: Path) -> None:
        p = tmp_path / "range.txt"
        p.write_text("a\nb\nc\nd\ne", encoding="utf-8")
        result = tagger.read_range(p, 2, 4)
        assert len(result.lines) == 3
        assert result.lines[0].number == 2
        assert result.lines[0].content == "b"
        assert result.lines[2].number == 4
        assert result.lines[2].content == "d"


class TestIsBinary:
    def test_text_file(self, tagger: HashlineTagger, tmp_path: Path) -> None:
        p = tmp_path / "text.txt"
        p.write_text("hello world", encoding="utf-8")
        assert tagger.is_binary(p) is False

    def test_binary_file(self, tagger: HashlineTagger, tmp_path: Path) -> None:
        p = tmp_path / "bin.dat"
        p.write_bytes(b"data\x00more")
        assert tagger.is_binary(p) is True
