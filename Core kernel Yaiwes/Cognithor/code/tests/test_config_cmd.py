"""Tests for cognithor.cli.config_cmd -- non-interactive config commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import yaml

from cognithor.cli.config_cmd import (
    _DISPLAY_FIELDS,
    _SENTINEL,
    _get_nested,
    _load_config,
    _save_config,
    _set_nested,
    cmd_get,
    cmd_list,
    cmd_set,
)

if TYPE_CHECKING:
    from pathlib import Path

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


@pytest.fixture()
def tmp_config(tmp_path: Path) -> Path:
    """Create a minimal config YAML in a temp dir."""
    cfg = tmp_path / "config.yaml"
    data = {
        "llm_backend_type": "ollama",
        "api_port": 8741,
        "language": "de",
        "operation_mode": "offline",
        "owner_name": "Tester",
        "models": {
            "planner": {"name": "qwen3:32b"},
            "executor": {"name": "qwen3:32b"},
        },
    }
    cfg.write_text(yaml.safe_dump(data), encoding="utf-8")
    return cfg


@pytest.fixture()
def empty_config(tmp_path: Path) -> Path:
    """Create an empty config YAML."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text("{}\n", encoding="utf-8")
    return cfg


# ------------------------------------------------------------------
# _get_nested / _set_nested
# ------------------------------------------------------------------


class TestGetNested:
    def test_top_level(self) -> None:
        assert _get_nested({"a": 1}, "a") == 1

    def test_nested(self) -> None:
        assert _get_nested({"a": {"b": {"c": 3}}}, "a.b.c") == 3

    def test_missing_returns_sentinel(self) -> None:
        assert _get_nested({}, "x.y") is _SENTINEL

    def test_non_dict_intermediate(self) -> None:
        assert _get_nested({"a": 42}, "a.b") is _SENTINEL


class TestSetNested:
    def test_simple(self) -> None:
        d: dict = {}
        _set_nested(d, "x", "hello")
        assert d == {"x": "hello"}

    def test_deep(self) -> None:
        d: dict = {}
        _set_nested(d, "a.b.c", "val")
        assert d == {"a": {"b": {"c": "val"}}}

    def test_numeric_string_auto_converts(self) -> None:
        d: dict = {}
        _set_nested(d, "port", "8080")
        assert d["port"] == 8080

    def test_overwrites_existing(self) -> None:
        d = {"k": "old"}
        _set_nested(d, "k", "new")
        assert d["k"] == "new"


# ------------------------------------------------------------------
# _load_config / _save_config
# ------------------------------------------------------------------


class TestLoadSave:
    def test_round_trip(self, tmp_path: Path) -> None:
        cfg = tmp_path / "rt.yaml"
        original = {"a": 1, "b": {"c": "hello"}}
        cfg.write_text(yaml.safe_dump(original), encoding="utf-8")
        loaded = _load_config(cfg)
        assert loaded == original

    def test_save_creates_parent(self, tmp_path: Path) -> None:
        cfg = tmp_path / "sub" / "dir" / "config.yaml"
        _save_config({"x": 1}, cfg)
        assert cfg.exists()
        loaded = _load_config(cfg)
        assert loaded["x"] == 1

    def test_load_empty_returns_dict(self, tmp_path: Path) -> None:
        cfg = tmp_path / "empty.yaml"
        cfg.write_text("", encoding="utf-8")
        assert _load_config(cfg) == {}


# ------------------------------------------------------------------
# Public commands
# ------------------------------------------------------------------


class TestCmdGet:
    def test_existing_key(self, tmp_config: Path) -> None:
        assert cmd_get("llm_backend_type", config_path=tmp_config) == 0

    def test_nested_key(self, tmp_config: Path) -> None:
        assert cmd_get("models.planner.name", config_path=tmp_config) == 0

    def test_missing_key(self, tmp_config: Path) -> None:
        assert cmd_get("nonexistent.key", config_path=tmp_config) == 1


class TestCmdSet:
    def test_set_top_level(self, tmp_config: Path) -> None:
        assert cmd_set("language", "en", config_path=tmp_config) == 0
        data = _load_config(tmp_config)
        assert data["language"] == "en"

    def test_set_nested(self, tmp_config: Path) -> None:
        assert cmd_set("models.planner.name", "gpt-4o", config_path=tmp_config) == 0
        data = _load_config(tmp_config)
        assert data["models"]["planner"]["name"] == "gpt-4o"

    def test_set_numeric(self, tmp_config: Path) -> None:
        assert cmd_set("api_port", "9999", config_path=tmp_config) == 0
        data = _load_config(tmp_config)
        assert data["api_port"] == 9999


class TestCmdList:
    def test_returns_zero(self, tmp_config: Path) -> None:
        assert cmd_list(config_path=tmp_config) == 0

    def test_empty_config(self, empty_config: Path) -> None:
        assert cmd_list(config_path=empty_config) == 0


# ------------------------------------------------------------------
# Display fields
# ------------------------------------------------------------------


def test_display_fields_count() -> None:
    assert len(_DISPLAY_FIELDS) == 7


def test_display_fields_are_tuples() -> None:
    for item in _DISPLAY_FIELDS:
        assert isinstance(item, tuple)
        assert len(item) == 2
