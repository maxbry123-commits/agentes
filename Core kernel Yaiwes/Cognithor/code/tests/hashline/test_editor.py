# Copyright 2024-2026 Cognithor Contributors
# Licensed under the Apache License, Version 2.0
"""Tests for HashlineEditor."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from cognithor.hashline.editor import HashlineEditor
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


@pytest.fixture
def editor(
    validator: HashlineValidator,
    cache: HashlineCache,
    hasher: LineHasher,
    config: HashlineConfig,
) -> HashlineEditor:
    return HashlineEditor(validator, cache, hasher, config)


def _tag_file(tagger: HashlineTagger, path: Path) -> list[tuple[int, str, str]]:
    data = tagger.read_and_tag(path)
    return [(line.number, line.hash_tag, line.content) for line in data.lines]


class TestReplace:
    def test_replace_line(
        self,
        editor: HashlineEditor,
        tagger: HashlineTagger,
        tmp_path: Path,
    ) -> None:
        p = tmp_path / "replace.py"
        p.write_text("hello\nworld\nfoo", encoding="utf-8")
        lines = _tag_file(tagger, p)
        intent = EditIntent(
            file_path=p,
            target_line=2,
            target_hash=lines[1][1],
            operation="replace",
            new_content="earth",
        )
        result = editor.execute_edit(intent)
        assert result.success is True
        assert result.old_content == "world"
        content = p.read_text(encoding="utf-8")
        assert "earth" in content
        assert "world" not in content


class TestInsertAfter:
    def test_insert_after_line(
        self,
        editor: HashlineEditor,
        tagger: HashlineTagger,
        tmp_path: Path,
    ) -> None:
        p = tmp_path / "insert_after.py"
        p.write_text("a\nb\nc", encoding="utf-8")
        lines = _tag_file(tagger, p)
        intent = EditIntent(
            file_path=p,
            target_line=2,
            target_hash=lines[1][1],
            operation="insert_after",
            new_content="b2",
        )
        result = editor.execute_edit(intent)
        assert result.success is True
        content = p.read_text(encoding="utf-8").split("\n")
        assert content == ["a", "b", "b2", "c"]


class TestInsertBefore:
    def test_insert_before_line(
        self,
        editor: HashlineEditor,
        tagger: HashlineTagger,
        tmp_path: Path,
    ) -> None:
        p = tmp_path / "insert_before.py"
        p.write_text("a\nb\nc", encoding="utf-8")
        lines = _tag_file(tagger, p)
        intent = EditIntent(
            file_path=p,
            target_line=2,
            target_hash=lines[1][1],
            operation="insert_before",
            new_content="b0",
        )
        result = editor.execute_edit(intent)
        assert result.success is True
        content = p.read_text(encoding="utf-8").split("\n")
        assert content == ["a", "b0", "b", "c"]


class TestDelete:
    def test_delete_line(
        self,
        editor: HashlineEditor,
        tagger: HashlineTagger,
        tmp_path: Path,
    ) -> None:
        p = tmp_path / "delete.py"
        p.write_text("a\nb\nc", encoding="utf-8")
        lines = _tag_file(tagger, p)
        intent = EditIntent(
            file_path=p,
            target_line=2,
            target_hash=lines[1][1],
            operation="delete",
            new_content=None,
        )
        result = editor.execute_edit(intent)
        assert result.success is True
        content = p.read_text(encoding="utf-8").split("\n")
        assert content == ["a", "c"]


class TestAtomicWrite:
    def test_preserves_content_on_success(
        self,
        editor: HashlineEditor,
        tagger: HashlineTagger,
        tmp_path: Path,
    ) -> None:
        p = tmp_path / "atomic.py"
        p.write_text("line1\nline2\nline3", encoding="utf-8")
        lines = _tag_file(tagger, p)
        intent = EditIntent(
            file_path=p,
            target_line=1,
            target_hash=lines[0][1],
            operation="replace",
            new_content="new_line1",
        )
        result = editor.execute_edit(intent)
        assert result.success is True
        assert p.read_text(encoding="utf-8") == "new_line1\nline2\nline3"

    def test_file_still_exists_after_edit(
        self,
        editor: HashlineEditor,
        tagger: HashlineTagger,
        tmp_path: Path,
    ) -> None:
        p = tmp_path / "exists.py"
        p.write_text("content", encoding="utf-8")
        lines = _tag_file(tagger, p)
        intent = EditIntent(
            file_path=p,
            target_line=1,
            target_hash=lines[0][1],
            operation="replace",
            new_content="new",
        )
        editor.execute_edit(intent)
        assert p.exists()


class TestEncodingPreservation:
    def test_preserves_utf8(
        self,
        editor: HashlineEditor,
        tagger: HashlineTagger,
        tmp_path: Path,
    ) -> None:
        p = tmp_path / "utf8.py"
        p.write_text("hello\nworld", encoding="utf-8")
        lines = _tag_file(tagger, p)
        intent = EditIntent(
            file_path=p,
            target_line=1,
            target_hash=lines[0][1],
            operation="replace",
            new_content="hi",
        )
        result = editor.execute_edit(intent)
        assert result.success is True
        # Should still be valid UTF-8
        p.read_text(encoding="utf-8")


class TestNewlinePreservation:
    def test_preserves_lf(
        self,
        editor: HashlineEditor,
        tagger: HashlineTagger,
        tmp_path: Path,
    ) -> None:
        p = tmp_path / "lf.py"
        p.write_bytes(b"a\nb\nc")
        lines = _tag_file(tagger, p)
        intent = EditIntent(
            file_path=p,
            target_line=1,
            target_hash=lines[0][1],
            operation="replace",
            new_content="x",
        )
        editor.execute_edit(intent)
        raw = p.read_bytes()
        assert b"\r\n" not in raw
        assert raw == b"x\nb\nc"

    def test_preserves_crlf(
        self,
        editor: HashlineEditor,
        tagger: HashlineTagger,
        tmp_path: Path,
    ) -> None:
        p = tmp_path / "crlf.py"
        p.write_bytes(b"a\r\nb\r\nc")
        lines = _tag_file(tagger, p)
        intent = EditIntent(
            file_path=p,
            target_line=1,
            target_hash=lines[0][1],
            operation="replace",
            new_content="x",
        )
        editor.execute_edit(intent)
        raw = p.read_bytes()
        assert b"\r\n" in raw


class TestInvalidEdit:
    def test_wrong_hash_returns_failure(
        self,
        editor: HashlineEditor,
        tagger: HashlineTagger,
        tmp_path: Path,
    ) -> None:
        p = tmp_path / "wrong.py"
        p.write_text("hello\nworld", encoding="utf-8")
        _tag_file(tagger, p)
        intent = EditIntent(
            file_path=p,
            target_line=1,
            target_hash="ZZ",
            operation="replace",
            new_content="nope",
        )
        result = editor.execute_edit(intent)
        assert result.success is False
        assert result.error is not None


class TestBatchEdit:
    def test_batch_multiple_edits(
        self,
        editor: HashlineEditor,
        tagger: HashlineTagger,
        tmp_path: Path,
    ) -> None:
        p = tmp_path / "batch.py"
        p.write_text("a\nb\nc\nd", encoding="utf-8")
        lines = _tag_file(tagger, p)
        intents = [
            EditIntent(
                file_path=p,
                target_line=2,
                target_hash=lines[1][1],
                operation="replace",
                new_content="B",
            ),
            EditIntent(
                file_path=p,
                target_line=4,
                target_hash=lines[3][1],
                operation="replace",
                new_content="D",
            ),
        ]
        results = editor.execute_batch(intents)
        assert all(r.success for r in results)
        content = p.read_text(encoding="utf-8").split("\n")
        assert "B" in content
        assert "D" in content
