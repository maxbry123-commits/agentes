# Copyright 2024-2026 Cognithor Contributors
# Licensed under the Apache License, Version 2.0
"""Tests for Hashline Guard formatter."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from cognithor.hashline.models import HashlinedFile, HashlinedLine

if TYPE_CHECKING:
    from cognithor.hashline.formatter import HashlineFormatter


class TestFormatLine:
    def test_single_line(self, formatter: HashlineFormatter) -> None:
        line = HashlinedLine(number=1, content="hello", hash_tag="AB", full_hash="0" * 16)
        result = formatter.format_line(line, line_width=1)
        assert result == "1#AB| hello"

    def test_line_number_padding(self, formatter: HashlineFormatter) -> None:
        line = HashlinedLine(number=5, content="world", hash_tag="Zz", full_hash="f" * 16)
        result = formatter.format_line(line, line_width=3)
        assert result == "  5#Zz| world"

    def test_empty_content(self, formatter: HashlineFormatter) -> None:
        line = HashlinedLine(number=10, content="", hash_tag="00", full_hash="a" * 16)
        result = formatter.format_line(line, line_width=2)
        assert result == "10#00| "


class TestFormatFile:
    def test_format_full_file(
        self, formatter: HashlineFormatter, sample_file: HashlinedFile
    ) -> None:
        result = formatter.format_file(sample_file)
        lines = result.split("\n")
        assert len(lines) == 5
        # First line should start with "1#"
        assert lines[0].startswith("1#")
        # Each line contains the separator "| "
        for line in lines:
            assert "| " in line

    def test_format_empty_file(self, formatter: HashlineFormatter) -> None:
        empty = HashlinedFile(
            path=Path("/tmp/empty.py"),
            lines=[],
            file_hash="0" * 64,
            read_timestamp=0.0,
            encoding="utf-8",
        )
        assert formatter.format_file(empty) == ""


class TestFormatRange:
    def test_format_range_subset(
        self, formatter: HashlineFormatter, sample_file: HashlinedFile
    ) -> None:
        result = formatter.format_range(sample_file, start=2, end=4)
        lines = result.split("\n")
        assert len(lines) == 3

    def test_format_range_single_line(
        self, formatter: HashlineFormatter, sample_file: HashlinedFile
    ) -> None:
        result = formatter.format_range(sample_file, start=1, end=1)
        lines = result.split("\n")
        assert len(lines) == 1


class TestParseReference:
    def test_valid_reference(self, formatter: HashlineFormatter) -> None:
        line_num, tag = formatter.parse_reference("22#XJ")
        assert line_num == 22
        assert tag == "XJ"

    def test_reference_with_whitespace(self, formatter: HashlineFormatter) -> None:
        line_num, tag = formatter.parse_reference("  5#Ab  ")
        assert line_num == 5
        assert tag == "Ab"

    def test_invalid_reference(self, formatter: HashlineFormatter) -> None:
        with pytest.raises(ValueError, match="Invalid line reference"):
            formatter.parse_reference("not-a-ref")

    def test_invalid_tag_length(self, formatter: HashlineFormatter) -> None:
        with pytest.raises(ValueError):
            formatter.parse_reference("22#ABC")  # 3 chars, not 2


class TestParseEditCommand:
    def test_replace(self, formatter: HashlineFormatter) -> None:
        intent = formatter.parse_edit_command("REPLACE 22#XJ src/main.py: new content here")
        assert intent.operation == "replace"
        assert intent.target_line == 22
        assert intent.target_hash == "XJ"
        assert intent.file_path == Path("src/main.py")
        assert intent.new_content == "new content here"

    def test_delete(self, formatter: HashlineFormatter) -> None:
        intent = formatter.parse_edit_command("DELETE 5#Ab src/old.py")
        assert intent.operation == "delete"
        assert intent.target_line == 5
        assert intent.target_hash == "Ab"
        assert intent.new_content is None

    def test_insert_after(self, formatter: HashlineFormatter) -> None:
        intent = formatter.parse_edit_command("INSERT_AFTER 10#Zz lib/utils.py: added line")
        assert intent.operation == "insert_after"
        assert intent.new_content == "added line"

    def test_invalid_command(self, formatter: HashlineFormatter) -> None:
        with pytest.raises(ValueError, match="Invalid edit command"):
            formatter.parse_edit_command("UNKNOWN 1#AB file.py: content")
