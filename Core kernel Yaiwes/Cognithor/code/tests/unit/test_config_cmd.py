"""Tests for cognithor.cli.config_cmd — get / set / list commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import yaml

from cognithor.cli.config_cmd import _load_config, cmd_get, cmd_list, cmd_set

if TYPE_CHECKING:
    from pathlib import Path

_SAMPLE = {
    "llm_backend_type": "ollama",
    "api_port": 8741,
    "language": "de",
    "operation_mode": "normal",
    "owner_name": "Alexander",
    "models": {
        "planner": {"name": "qwen3:32b"},
        "executor": {"name": "qwen3:32b"},
    },
}


@pytest.fixture()
def tmp_config(tmp_path: Path) -> Path:
    """Create a temporary config.yaml pre-filled with sample data."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.safe_dump(_SAMPLE, default_flow_style=False), encoding="utf-8")
    return cfg


# ------------------------------------------------------------------
# cmd_get
# ------------------------------------------------------------------


def test_get_top_level(tmp_config: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = cmd_get("llm_backend_type", config_path=tmp_config)
    assert rc == 0
    assert "ollama" in capsys.readouterr().out


def test_get_nested(tmp_config: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = cmd_get("models.planner.name", config_path=tmp_config)
    assert rc == 0
    assert "qwen3:32b" in capsys.readouterr().out


def test_get_missing_key(tmp_config: Path) -> None:
    rc = cmd_get("no.such.key", config_path=tmp_config)
    assert rc == 1


# ------------------------------------------------------------------
# cmd_set
# ------------------------------------------------------------------


def test_set_top_level(tmp_config: Path) -> None:
    rc = cmd_set("language", "en", config_path=tmp_config)
    assert rc == 0
    data = _load_config(tmp_config)
    assert data["language"] == "en"


def test_set_nested(tmp_config: Path) -> None:
    rc = cmd_set("models.planner.name", "llama3:70b", config_path=tmp_config)
    assert rc == 0
    data = _load_config(tmp_config)
    assert data["models"]["planner"]["name"] == "llama3:70b"


def test_set_integer(tmp_config: Path) -> None:
    rc = cmd_set("api_port", "9000", config_path=tmp_config)
    assert rc == 0
    data = _load_config(tmp_config)
    assert data["api_port"] == 9000
    assert isinstance(data["api_port"], int)


# ------------------------------------------------------------------
# cmd_list
# ------------------------------------------------------------------


def test_list_shows_settings(tmp_config: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = cmd_list(config_path=tmp_config)
    assert rc == 0
    out = capsys.readouterr().out
    assert "ollama" in out
    assert "qwen3:32b" in out
    assert "8741" in out
    assert "Alexander" in out
