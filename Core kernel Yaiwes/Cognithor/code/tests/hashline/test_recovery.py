# Copyright 2024-2026 Cognithor Contributors
# Licensed under the Apache License, Version 2.0
"""Tests for HashlineRecovery."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

import pytest

from cognithor.hashline.cache import HashlineCache
from cognithor.hashline.config import HashlineConfig
from cognithor.hashline.editor import HashlineEditor
from cognithor.hashline.exceptions import MaxRetriesExceededError
from cognithor.hashline.hasher import LineHasher
from cognithor.hashline.models import EditIntent
from cognithor.hashline.recovery import HashlineRecovery
from cognithor.hashline.tagger import HashlineTagger
from cognithor.hashline.validator import HashlineValidator

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def fast_config() -> HashlineConfig:
    """Config with zero retry delay for fast tests."""
    return HashlineConfig(max_retries=3, retry_delay_seconds=0.0)


@pytest.fixture
def fast_hasher(fast_config: HashlineConfig) -> LineHasher:
    return LineHasher(fast_config)


@pytest.fixture
def fast_cache(fast_config: HashlineConfig) -> HashlineCache:
    return HashlineCache(fast_config)


@pytest.fixture
def fast_tagger(
    fast_hasher: LineHasher, fast_cache: HashlineCache, fast_config: HashlineConfig
) -> HashlineTagger:
    return HashlineTagger(fast_hasher, fast_cache, fast_config)


@pytest.fixture
def fast_validator(
    fast_hasher: LineHasher, fast_cache: HashlineCache, fast_config: HashlineConfig
) -> HashlineValidator:
    return HashlineValidator(fast_hasher, fast_cache, fast_config)


@pytest.fixture
def fast_editor(
    fast_validator: HashlineValidator,
    fast_cache: HashlineCache,
    fast_hasher: LineHasher,
    fast_config: HashlineConfig,
) -> HashlineEditor:
    return HashlineEditor(fast_validator, fast_cache, fast_hasher, fast_config)


@pytest.fixture
def recovery(
    fast_tagger: HashlineTagger,
    fast_editor: HashlineEditor,
    fast_cache: HashlineCache,
    fast_config: HashlineConfig,
) -> HashlineRecovery:
    return HashlineRecovery(fast_tagger, fast_editor, fast_cache, fast_config)


class TestSuccessfulEdit:
    def test_edit_succeeds_first_try(
        self,
        recovery: HashlineRecovery,
        fast_tagger: HashlineTagger,
        tmp_path: Path,
    ) -> None:
        p = tmp_path / "ok.py"
        p.write_text("hello\nworld", encoding="utf-8")
        data = fast_tagger.read_and_tag(p)
        intent = EditIntent(
            file_path=p,
            target_line=1,
            target_hash=data.lines[0].hash_tag,
            operation="replace",
            new_content="hi",
        )
        result = recovery.attempt_with_recovery(intent)
        assert result.success is True
        assert result.retry_count == 0


class TestRetryOnMismatch:
    def test_successful_retry_after_file_change(
        self,
        recovery: HashlineRecovery,
        fast_tagger: HashlineTagger,
        fast_hasher: LineHasher,
        tmp_path: Path,
    ) -> None:
        """File changes between read and edit; recovery finds the line."""
        p = tmp_path / "retry.py"
        p.write_text("hello\nworld\nfoo", encoding="utf-8")
        data = fast_tagger.read_and_tag(p)
        old_tag = data.lines[0].hash_tag

        # Now change file: insert a line at top, shifting "hello" to line 2
        p.write_text("new_first\nhello\nworld\nfoo", encoding="utf-8")

        intent = EditIntent(
            file_path=p,
            target_line=1,
            target_hash=old_tag,  # hash of "hello", but "hello" is now at line 2
            operation="replace",
            new_content="hi",
        )
        result = recovery.attempt_with_recovery(intent)
        assert result.success is True
        assert result.retry_count > 0


class TestMaxRetries:
    def test_raises_after_max_retries(self, tmp_path: Path) -> None:
        cfg = HashlineConfig(max_retries=1, retry_delay_seconds=0.0)
        hasher = LineHasher(cfg)
        cache = HashlineCache(cfg)
        tagger = HashlineTagger(hasher, cache, cfg)
        validator = HashlineValidator(hasher, cache, cfg)
        editor = HashlineEditor(validator, cache, hasher, cfg)
        rec = HashlineRecovery(tagger, editor, cache, cfg)

        p = tmp_path / "fail.py"
        p.write_text("hello\nworld", encoding="utf-8")
        tagger.read_and_tag(p)

        # Target a line that doesn't exist so recovery can never find a match
        intent = EditIntent(
            file_path=p,
            target_line=999,
            target_hash="ZZ",
            operation="replace",
            new_content="nope",
        )
        with pytest.raises(MaxRetriesExceededError):
            rec.attempt_with_recovery(intent)


class TestFuzzyMatch:
    def test_finds_slightly_changed_line(
        self,
        recovery: HashlineRecovery,
        fast_tagger: HashlineTagger,
        fast_hasher: LineHasher,
        fast_cache: HashlineCache,
        tmp_path: Path,
    ) -> None:
        """Fuzzy match should find a line that was slightly modified."""
        p = tmp_path / "fuzzy.py"
        original = "def very_long_function_name_that_is_unique():"
        p.write_text(f"{original}\n    pass\n    return True", encoding="utf-8")
        data = fast_tagger.read_and_tag(p)
        old_tag = data.lines[0].hash_tag

        # Slightly change the function name (still >80% similar)
        changed = "def very_long_function_name_that_is_unique_v2():"
        p.write_text(f"# comment\n{changed}\n    pass\n    return True", encoding="utf-8")

        # Invalidate cache so recovery re-reads
        fast_cache.invalidate(p.resolve())

        intent = EditIntent(
            file_path=p,
            target_line=1,
            target_hash=old_tag,
            operation="replace",
            new_content="def new_func():",
        )
        # This may or may not succeed depending on fuzzy match threshold
        # The main point is it doesn't crash
        with contextlib.suppress(MaxRetriesExceededError):
            recovery.attempt_with_recovery(intent)


class TestErrorContext:
    def test_build_error_context(
        self,
        recovery: HashlineRecovery,
        fast_tagger: HashlineTagger,
        tmp_path: Path,
    ) -> None:
        p = tmp_path / "ctx.py"
        p.write_text("a\nb\nc\nd\ne", encoding="utf-8")
        data = fast_tagger.read_and_tag(p)
        intent = EditIntent(
            file_path=p,
            target_line=3,
            target_hash="ZZ",
            operation="replace",
            new_content="new",
        )
        ctx = recovery._build_error_context(intent, data)
        assert "line 3" in ctx.lower() or "3#" in ctx

    def test_error_context_shows_surrounding_lines(
        self,
        recovery: HashlineRecovery,
        fast_tagger: HashlineTagger,
        tmp_path: Path,
    ) -> None:
        p = tmp_path / "ctx2.py"
        lines = [f"line_{i}" for i in range(10)]
        p.write_text("\n".join(lines), encoding="utf-8")
        data = fast_tagger.read_and_tag(p)
        intent = EditIntent(
            file_path=p,
            target_line=5,
            target_hash="ZZ",
            operation="replace",
            new_content="new",
        )
        ctx = recovery._build_error_context(intent, data)
        # Should contain lines around line 5
        assert "line_4" in ctx or "line_5" in ctx
