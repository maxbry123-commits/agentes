# Copyright 2024-2026 Cognithor Contributors
# Licensed under the Apache License, Version 2.0
"""Hashline Guard — output formatting and command parsing."""

from __future__ import annotations

import re
from pathlib import Path

from cognithor.hashline.models import EditIntent, HashlinedFile, HashlinedLine
from cognithor.utils.logging import get_logger

log = get_logger(__name__)

# Pattern: "22#XJ" — line number, hash separator, 2-char tag
_REFERENCE_RE = re.compile(r"^(\d+)#([A-Za-z0-9]{2})$")

# Pattern for edit commands:
#   REPLACE 22#XJ path/to/file.py: new content
#   INSERT_AFTER 22#XJ path/to/file.py: new content
#   INSERT_BEFORE 22#XJ path/to/file.py: new content
#   DELETE 22#XJ path/to/file.py
_EDIT_CMD_RE = re.compile(
    r"^(REPLACE|INSERT_AFTER|INSERT_BEFORE|DELETE)\s+"
    r"(\d+)#([A-Za-z0-9]{2})\s+"
    r"(\S+)"
    r"(?::\s*(.*))?$",
    re.DOTALL,
)


class HashlineFormatter:
    """Formats hashlined file data for display and parses edit commands.

    The display format for each line is::

        {num}#{tag}| {content}

    Where ``num`` is right-aligned to the width of the largest line number,
    and ``tag`` is exactly 2 characters.
    """

    def format_file(self, data: HashlinedFile) -> str:
        """Format an entire hashlined file for display.

        Args:
            data: The hashlined file data.

        Returns:
            Multi-line string with all lines formatted.
        """
        if not data.lines:
            return ""
        line_width = len(str(data.lines[-1].number))
        parts: list[str] = []
        for line in data.lines:
            parts.append(self.format_line(line, line_width))
        return "\n".join(parts)

    def format_range(self, data: HashlinedFile, start: int, end: int) -> str:
        """Format a range of lines from a hashlined file.

        Args:
            data: The hashlined file data.
            start: 1-based start line number (inclusive).
            end: 1-based end line number (inclusive).

        Returns:
            Multi-line string with the selected lines formatted.
        """
        if not data.lines:
            return ""
        # Determine line width based on the full file for consistent alignment
        line_width = len(str(data.lines[-1].number))
        parts: list[str] = []
        for line in data.lines:
            if start <= line.number <= end:
                parts.append(self.format_line(line, line_width))
        return "\n".join(parts)

    def format_line(self, line: HashlinedLine, line_width: int) -> str:
        """Format a single hashlined line.

        Args:
            line: The hashlined line data.
            line_width: Width for right-aligning the line number.

        Returns:
            Formatted string: ``{num}#{tag}| {content}``.
        """
        num = str(line.number).rjust(line_width)
        return f"{num}#{line.hash_tag}| {line.content}"

    @staticmethod
    def parse_reference(ref: str) -> tuple[int, str]:
        """Parse a line reference like ``22#XJ``.

        Args:
            ref: Reference string in the format ``{line_number}#{tag}``.

        Returns:
            Tuple of (line_number, hash_tag).

        Raises:
            ValueError: If the reference format is invalid.
        """
        m = _REFERENCE_RE.match(ref.strip())
        if not m:
            raise ValueError(f"Invalid line reference: {ref!r}. Expected format: '22#XJ'")
        return int(m.group(1)), m.group(2)

    @staticmethod
    def parse_edit_command(command: str) -> EditIntent:
        """Parse an edit command string into an EditIntent.

        Supported formats::

            REPLACE 22#XJ path/to/file.py: new content here
            INSERT_AFTER 22#XJ path/to/file.py: new content here
            INSERT_BEFORE 22#XJ path/to/file.py: new content here
            DELETE 22#XJ path/to/file.py

        Args:
            command: The edit command string.

        Returns:
            An ``EditIntent`` describing the intended operation.

        Raises:
            ValueError: If the command format is invalid.
        """
        m = _EDIT_CMD_RE.match(command.strip())
        if not m:
            raise ValueError(
                f"Invalid edit command: {command!r}. "
                "Expected: REPLACE|INSERT_AFTER|INSERT_BEFORE|DELETE "
                "{line}#{tag} {path}[: content]"
            )
        operation_raw = m.group(1)
        line_number = int(m.group(2))
        tag = m.group(3)
        file_path = Path(m.group(4))
        new_content = m.group(5)

        # Normalize operation name to lowercase with underscores
        operation = operation_raw.lower()

        return EditIntent(
            file_path=file_path,
            target_line=line_number,
            target_hash=tag,
            operation=operation,
            new_content=new_content,
        )
