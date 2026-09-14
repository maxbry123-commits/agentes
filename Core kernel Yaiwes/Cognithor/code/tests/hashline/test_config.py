# Copyright 2024-2026 Cognithor Contributors
# Licensed under the Apache License, Version 2.0
"""Tests for Hashline Guard configuration."""

from __future__ import annotations

from pathlib import Path

from cognithor.hashline.config import HashlineConfig


class TestConfigDefault:
    def test_default_values(self) -> None:
        cfg = HashlineConfig.default()
        assert cfg.enabled is True
        assert cfg.hash_algorithm == "xxhash64"
        assert cfg.tag_length == 2
        assert cfg.max_file_size_mb == 10.0
        assert cfg.max_retries == 3
        assert cfg.cache_max_files == 100
        assert cfg.binary_detection is True
        assert cfg.audit_enabled is True

    def test_tag_charset_length(self) -> None:
        cfg = HashlineConfig.default()
        assert len(cfg.tag_charset) == 62


class TestConfigFromDict:
    def test_partial_override(self) -> None:
        cfg = HashlineConfig.from_dict({"max_retries": 5, "enabled": False})
        assert cfg.max_retries == 5
        assert cfg.enabled is False
        # Defaults remain
        assert cfg.tag_length == 2

    def test_unknown_keys_ignored(self) -> None:
        cfg = HashlineConfig.from_dict({"nonexistent_key": "value", "enabled": True})
        assert cfg.enabled is True

    def test_empty_dict(self) -> None:
        cfg = HashlineConfig.from_dict({})
        assert cfg == HashlineConfig.default()


class TestConfigExcluded:
    def test_excluded_pyc(self) -> None:
        cfg = HashlineConfig.default()
        assert cfg.is_excluded(Path("module.pyc")) is True

    def test_excluded_git(self) -> None:
        cfg = HashlineConfig.default()
        assert cfg.is_excluded(Path(".git/config")) is True

    def test_not_excluded_py(self) -> None:
        cfg = HashlineConfig.default()
        assert cfg.is_excluded(Path("main.py")) is False

    def test_excluded_node_modules(self) -> None:
        cfg = HashlineConfig.default()
        assert cfg.is_excluded(Path("node_modules/pkg/index.js")) is True


class TestConfigProtected:
    def test_protected_env(self) -> None:
        cfg = HashlineConfig.default()
        assert cfg.is_protected(Path(".env")) is True

    def test_protected_pem(self) -> None:
        cfg = HashlineConfig.default()
        assert cfg.is_protected(Path("server.pem")) is True

    def test_protected_credentials(self) -> None:
        cfg = HashlineConfig.default()
        assert cfg.is_protected(Path("credentials.json")) is True

    def test_not_protected_normal(self) -> None:
        cfg = HashlineConfig.default()
        assert cfg.is_protected(Path("main.py")) is False
