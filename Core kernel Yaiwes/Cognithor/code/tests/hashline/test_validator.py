# Copyright 2024-2026 Cognithor Contributors
# Licensed under the Apache License, Version 2.0
"""Tests for HashlineValidator."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from cognithor.hashline.models import EditIntent
from cognithor.hashline.tagger import HashlineTagger
from cognithor.hashline.validator import HashlineValidator

if TYPE_CHECKING:
    from pathlib import Path

    from cognithor.hashline.cache import HashlineCache
    from cognithor.hashline.config import HashlineConfig
    from cognithor.hashline.hasher import LineHasher


@pytest.fixture
def tagger(config: HashlineConfig, hasher: LineHasher, cache: HashlineCache) -> HashlineTagger:
    return HashlineTagger(hasher, cache, config)


@pytest.fixture
def validator(
    hasher: LineHasher, cache: HashlineCache, config: HashlineConfig
) -> HashlineValidator:
    return HashlineValidator(hasher, cache, config)


def _write_and_tag(tagger: HashlineTagger, path: Path, content: str) -> list[tuple[int, str, str]]:
    """Write content to file, tag it, return list of (line_num, tag, content)."""
    path.write_text(content, encoding="utf-8")
    data = tagger.read_and_tag(path)
    return [(line.number, line.hash_tag, line.content) for line in data.lines]


class TestValidateEdit:
    def test_valid_edit(
        self,
        validator: HashlineValidator,
        tagger: HashlineTagger,
        tmp_path: Path,
    ) -> None:
        p = tmp_path / "valid.py"
        lines = _write_and_tag(tagger, p, "hello\nworld\n")
        intent = EditIntent(
            file_path=p,
            target_line=1,
            target_hash=lines[0][1],
            operation="replace",
            new_content="hi",
        )
        result = validator.validate_edit(intent)
        assert result.valid is True
        assert result.current_hash == lines[0][1]

    def test_hash_mismatch(
        self,
        validator: HashlineValidator,
        tagger: HashlineTagger,
        tmp_path: Path,
    ) -> None:
        p = tmp_path / "mismatch.py"
        _write_and_tag(tagger, p, "hello\nworld\n")
        intent = EditIntent(
            file_path=p,
            target_line=1,
            target_hash="ZZ",  # wrong hash
            operation="replace",
            new_content="hi",
        )
        result = validator.validate_edit(intent)
        assert result.valid is False
        assert "mismatch" in result.reason.lower()

    def test_auto_load_uncached(
        self,
        validator: HashlineValidator,
        tmp_path: Path,
        hasher: LineHasher,
    ) -> None:
        """Files not in cache should be auto-loaded, not rejected."""
        p = tmp_path / "uncached.py"
        p.write_text("hello\nworld", encoding="utf-8")
        tag, _ = hasher.hash_line("hello")
        intent = EditIntent(
            file_path=p,
            target_line=1,
            target_hash=tag,
            operation="replace",
            new_content="hi",
        )
        result = validator.validate_edit(intent)
        assert result.valid is True

    def test_line_out_of_range(
        self,
        validator: HashlineValidator,
        tagger: HashlineTagger,
        tmp_path: Path,
    ) -> None:
        p = tmp_path / "short.py"
        _write_and_tag(tagger, p, "only one line")
        intent = EditIntent(
            file_path=p,
            target_line=999,
            target_hash="AB",
            operation="replace",
            new_content="hi",
        )
        result = validator.validate_edit(intent)
        assert result.valid is False
        assert "does not exist" in result.reason.lower()

    def test_disk_change_detected(
        self,
        validator: HashlineValidator,
        tagger: HashlineTagger,
        tmp_path: Path,
        hasher: LineHasher,
    ) -> None:
        """If file changes on disk after caching, validation should detect it."""
        p = tmp_path / "changes.py"
        lines = _write_and_tag(tagger, p, "hello\nworld")
        # Modify file on disk
        p.write_text("changed\nworld", encoding="utf-8")
        intent = EditIntent(
            file_path=p,
            target_line=1,
            target_hash=lines[0][1],  # old hash
            operation="replace",
            new_content="hi",
        )
        result = validator.validate_edit(intent)
        assert result.valid is False


class TestValidateBatch:
    def test_batch_sorted_descending(
        self,
        validator: HashlineValidator,
        tagger: HashlineTagger,
        tmp_path: Path,
    ) -> None:
        p = tmp_path / "batch.py"
        lines = _write_and_tag(tagger, p, "a\nb\nc\nd")
        intents = [
            EditIntent(
                file_path=p,
                target_line=lines[i][0],
                target_hash=lines[i][1],
                operation="replace",
                new_content=f"new_{i}",
            )
            for i in [0, 2, 1]  # out of order
        ]
        results = validator.validate_batch(intents)
        # Results should be in descending line order
        assert len(results) == 3

    def test_batch_all_valid(
        self,
        validator: HashlineValidator,
        tagger: HashlineTagger,
        tmp_path: Path,
    ) -> None:
        p = tmp_path / "batch_valid.py"
        lines = _write_and_tag(tagger, p, "a\nb\nc")
        intents = [
            EditIntent(
                file_path=p,
                target_line=lines[i][0],
                target_hash=lines[i][1],
                operation="replace",
                new_content=f"new_{i}",
            )
            for i in range(3)
        ]
        results = validator.validate_batch(intents)
        assert all(r.valid for r in results)

    def test_batch_mixed_valid_invalid(
        self,
        validator: HashlineValidator,
        tagger: HashlineTagger,
        tmp_path: Path,
    ) -> None:
        p = tmp_path / "batch_mixed.py"
        lines = _write_and_tag(tagger, p, "a\nb\nc")
        intents = [
            EditIntent(
                file_path=p,
                target_line=1,
                target_hash=lines[0][1],
                operation="replace",
                new_content="ok",
            ),
            EditIntent(
                file_path=p,
                target_line=2,
                target_hash="ZZ",  # wrong
                operation="replace",
                new_content="bad",
            ),
        ]
        results = validator.validate_batch(intents)
        # One should be valid, one invalid
        valid_count = sum(1 for r in results if r.valid)
        invalid_count = sum(1 for r in results if not r.valid)
        assert valid_count == 1
        assert invalid_count == 1


class TestReadLineFromDisk:
    def test_reads_correct_line(
        self,
        validator: HashlineValidator,
        tmp_path: Path,
    ) -> None:
        p = tmp_path / "diskread.py"
        p.write_text("first\nsecond\nthird", encoding="utf-8")
        line = validator._read_line_from_disk(p, 2)
        assert line == "second"

    def test_returns_none_for_invalid_line(
        self,
        validator: HashlineValidator,
        tmp_path: Path,
    ) -> None:
        p = tmp_path / "short.py"
        p.write_text("only", encoding="utf-8")
        line = validator._read_line_from_disk(p, 99)
        assert line is None
