# Copyright 2024-2026 Cognithor Contributors
# Licensed under the Apache License, Version 2.0
"""Shared fixtures for Hashline Guard tests."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest

from cognithor.hashline.cache import HashlineCache
from cognithor.hashline.config import HashlineConfig
from cognithor.hashline.formatter import HashlineFormatter
from cognithor.hashline.hasher import LineHasher
from cognithor.hashline.models import HashlinedFile, HashlinedLine

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def config() -> HashlineConfig:
    """Default hashline configuration."""
    return HashlineConfig.default()


@pytest.fixture
def small_cache_config() -> HashlineConfig:
    """Config with a very small cache for eviction tests."""
    return HashlineConfig(cache_max_files=3, stale_threshold_seconds=1.0)


@pytest.fixture
def hasher(config: HashlineConfig) -> LineHasher:
    """LineHasher with default config."""
    return LineHasher(config)


@pytest.fixture
def cache(config: HashlineConfig) -> HashlineCache:
    """HashlineCache with default config."""
    return HashlineCache(config)


@pytest.fixture
def small_cache(small_cache_config: HashlineConfig) -> HashlineCache:
    """HashlineCache with max 3 files."""
    return HashlineCache(small_cache_config)


@pytest.fixture
def formatter() -> HashlineFormatter:
    """HashlineFormatter instance."""
    return HashlineFormatter()


@pytest.fixture
def sample_file(hasher: LineHasher, tmp_path: Path) -> HashlinedFile:
    """A sample hashlined file with 5 lines."""
    contents = [
        "def hello():",
        '    print("Hello, world!")',
        "",
        "def goodbye():",
        '    print("Goodbye!")',
    ]
    lines: list[HashlinedLine] = []
    for i, content in enumerate(contents, start=1):
        tag, full_hash = hasher.hash_line(content)
        lines.append(HashlinedLine(number=i, content=content, hash_tag=tag, full_hash=full_hash))

    file_path = tmp_path / "sample.py"
    file_path.write_text("\n".join(contents), encoding="utf-8")
    file_hash = hasher.hash_file(file_path)

    return HashlinedFile(
        path=file_path.resolve(),
        lines=lines,
        file_hash=file_hash,
        read_timestamp=time.time(),
        encoding="utf-8",
    )
