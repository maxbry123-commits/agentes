"""Tests fuer skills/cli.py -- Skills-CLI."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from cognithor.skills.cli import main

if TYPE_CHECKING:
    from pathlib import Path

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_config(tmp_path: Path):
    """Mocks load_config to return a config with tmp_path skills dir."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    config = MagicMock()
    config.cognithor_home = tmp_path
    config.plugins.skills_dir = "skills"

    with patch("cognithor.skills.cli.load_config", return_value=config):
        yield config, skills_dir


# ============================================================================
# list command
# ============================================================================


class TestListCommand:
    def test_list_no_skills(self, mock_config, capsys) -> None:
        _, skills_dir = mock_config
        main(["list"])
        captured = capsys.readouterr()
        assert "Keine Skills" in captured.out

    def test_list_with_skills(self, mock_config, capsys) -> None:
        _, skills_dir = mock_config
        (skills_dir / "skill-a.md").write_text("# A")
        (skills_dir / "skill-b.md").write_text("# B")
        main(["list"])
        captured = capsys.readouterr()
        assert "Installierte Skills" in captured.out
        assert "skill-a.md" in captured.out
        assert "skill-b.md" in captured.out


# ============================================================================
# create command
# ============================================================================


class TestCreateCommand:
    def test_create_skill(self, mock_config, capsys) -> None:
        _, skills_dir = mock_config
        main(["create", "Test Skill"])
        captured = capsys.readouterr()
        assert "erstellt" in captured.out
        assert (skills_dir / "test-skill.md").exists()

    def test_create_with_triggers(self, mock_config, capsys) -> None:
        _, skills_dir = mock_config
        main(["create", "Trigger Skill", "--triggers", "foo", "bar"])
        captured = capsys.readouterr()
        assert "erstellt" in captured.out
        content = (skills_dir / "trigger-skill.md").read_text(encoding="utf-8")
        assert "foo, bar" in content

    def test_create_duplicate_exits(self, mock_config) -> None:
        _, skills_dir = mock_config
        # Create first
        main(["create", "Doppelt"])
        # Create second should exit
        with pytest.raises(SystemExit):
            main(["create", "Doppelt"])


# ============================================================================
# search command
# ============================================================================


class TestSearchCommand:
    def test_search_no_results(self, mock_config, capsys) -> None:
        main(["search", "nonexistent-xyz"])
        captured = capsys.readouterr()
        assert "Keine Ergebnisse" in captured.out or "Gefundene" in captured.out

    def test_search_with_results(self, mock_config, capsys) -> None:
        with patch("cognithor.skills.manager.search_remote_skills", return_value=["found-skill"]):
            main(["search", "test"])
        captured = capsys.readouterr()
        assert "Gefundene Skills" in captured.out
        assert "found-skill" in captured.out

    def test_search_with_limit(self, mock_config, capsys) -> None:
        with patch("cognithor.skills.manager.search_remote_skills", return_value=[]) as mock_search:
            main(["search", "test", "--limit", "5"])
            mock_search.assert_called_once_with("test", limit=5)


# ============================================================================
# install command
# ============================================================================


class TestInstallCommand:
    def test_install_skill(self, mock_config, capsys) -> None:
        _, skills_dir = mock_config
        main(["install", "New Skill"])
        captured = capsys.readouterr()
        assert "installiert" in captured.out

    def test_install_with_repo(self, mock_config, capsys) -> None:
        _, skills_dir = mock_config
        main(["install", "Repo Skill", "--repo", "https://example.com"])
        captured = capsys.readouterr()
        assert "installiert" in captured.out


# ============================================================================
# Edge cases
# ============================================================================


class TestEdgeCases:
    def test_no_command_raises(self, mock_config) -> None:
        with pytest.raises(SystemExit):
            main([])

    def test_invalid_command_raises(self, mock_config) -> None:
        with pytest.raises(SystemExit):
            main(["invalid_command"])
