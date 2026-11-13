# Copyright 2024-2026 Cognithor Contributors
# Licensed under the Apache License, Version 2.0
"""Integration tests for Hashline Guard end-to-end flows."""

from __future__ import annotations

from pathlib import Path

import pytest

from cognithor.hashline import EditIntent, HashlineGuard
from cognithor.hashline.config import HashlineConfig


@pytest.fixture
def guard(tmp_path: Path) -> HashlineGuard:
    cfg = HashlineConfig(
        max_retries=2,
        retry_delay_seconds=0.0,
        audit_enabled=True,
    )
    return HashlineGuard.create(config=cfg, data_dir=tmp_path)


class TestFullReadEditVerify:
    def test_read_edit_verify_cycle(self, guard: HashlineGuard, tmp_path: Path) -> None:
        """Full cycle: read -> edit -> verify the edit was applied."""
        p = tmp_path / "cycle.py"
        p.write_text("def hello():\n    pass\n", encoding="utf-8")

        # Read
        output = guard.read_file(p)
        assert "hello" in output
        assert "#" in output  # has hash tags

        # Parse the hash tag for line 1
        # Format: " 1#XX| def hello():"
        first_line = output.split("\n")[0]
        tag = first_line.split("#")[1][:2]

        # Edit
        intent = EditIntent(
            file_path=p,
            target_line=1,
            target_hash=tag,
            operation="replace",
            new_content="def hi():",
        )
        result = guard.edit(intent)
        assert result.success is True

        # Verify
        new_output = guard.read_file(p)
        assert "hi()" in new_output
        assert "hello" not in new_output

    def test_read_range(self, guard: HashlineGuard, tmp_path: Path) -> None:
        p = tmp_path / "range.py"
        p.write_text("a\nb\nc\nd\ne", encoding="utf-8")
        output = guard.read_range(p, 2, 4)
        assert "b" in output
        assert "d" in output
        # Line 1 and 5 should not appear
        lines = output.strip().split("\n")
        assert len(lines) == 3


class TestConfigToggle:
    def test_disabled_guard_creation(self, tmp_path: Path) -> None:
        cfg = HashlineConfig(enabled=False)
        guard = HashlineGuard.create(config=cfg, data_dir=tmp_path)
        # Should still create the guard (enabled is checked at integration level)
        assert guard is not None

    def test_audit_disabled(self, tmp_path: Path) -> None:
        cfg = HashlineConfig(audit_enabled=False)
        guard = HashlineGuard.create(config=cfg, data_dir=tmp_path)
        assert guard._auditor is None

    def test_audit_enabled(self, tmp_path: Path) -> None:
        cfg = HashlineConfig(audit_enabled=True)
        guard = HashlineGuard.create(config=cfg, data_dir=tmp_path)
        assert guard._auditor is not None


class TestExcludedPatterns:
    def test_config_excludes_pyc(self) -> None:
        cfg = HashlineConfig()
        assert cfg.is_excluded(Path("module.pyc"))

    def test_config_excludes_git(self) -> None:
        cfg = HashlineConfig()
        assert cfg.is_excluded(Path(".git/config"))

    def test_config_does_not_exclude_py(self) -> None:
        cfg = HashlineConfig()
        assert not cfg.is_excluded(Path("module.py"))


class TestCacheStats:
    def test_stats_after_operations(self, guard: HashlineGuard, tmp_path: Path) -> None:
        p = tmp_path / "stats.py"
        p.write_text("hello", encoding="utf-8")
        guard.read_file(p)
        stats = guard.stats()
        assert stats["size"] >= 1

    def test_invalidate_clears_cache(self, guard: HashlineGuard, tmp_path: Path) -> None:
        p = tmp_path / "inval.py"
        p.write_text("hello", encoding="utf-8")
        guard.read_file(p)
        guard.invalidate(p)
        # After invalidate, we don't guarantee size is 0 because read_file caches
        # but the specific path should be removed
        # Reading again should still work
        output = guard.read_file(p)
        assert "hello" in output
