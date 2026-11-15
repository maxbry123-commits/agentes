"""Tests for the jarvis -> cognithor home directory migration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch


def _make_jarvis_home(base: Path) -> Path:
    """Create a fake ~/.jarvis/ structure under *base*."""
    jarvis = base / ".jarvis"
    jarvis.mkdir()
    # Directories
    for d in ("memory", "data", "vault", "skills", "config", "cache"):
        (jarvis / d).mkdir()
        (jarvis / d / "placeholder.txt").write_text(f"data in {d}")
    # Top-level files
    (jarvis / "config.yaml").write_text("language: de\n")
    (jarvis / "agents.yaml").write_text("agents: []\n")
    (jarvis / "CORE.md").write_text("# Core\n")
    return jarvis


class TestMigrateJarvisHome:
    """Tests for _migrate_jarvis_home()."""

    def test_migrate_jarvis_home(self, tmp_path: Path) -> None:
        """Full migration: dirs + files copied, marker written."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        _make_jarvis_home(fake_home)

        cognithor_home = fake_home / ".cognithor"
        cognithor_home.mkdir()

        with patch("cognithor.__main__.Path") as MockPath:
            # Path.home() -> fake_home, but Path(...) for other calls uses real Path
            MockPath.home.return_value = fake_home
            # For marker / dir creation we need real Path behavior
            MockPath.side_effect = Path

            # Re-import to avoid stale references — call the function directly
            from cognithor.__main__ import _migrate_jarvis_home

            _migrate_jarvis_home()

        # Verify directories were copied
        for d in ("memory", "data", "vault", "skills", "config", "cache"):
            assert (cognithor_home / d).is_dir(), f"{d}/ should be migrated"
            assert (cognithor_home / d / "placeholder.txt").exists()

        # Verify top-level files
        assert (cognithor_home / "config.yaml").read_text() == "language: de\n"
        assert (cognithor_home / "agents.yaml").read_text() == "agents: []\n"
        assert (cognithor_home / "CORE.md").read_text() == "# Core\n"

        # Marker exists
        marker = cognithor_home / ".migrated_from_jarvis"
        assert marker.exists()
        assert "memory" in marker.read_text()

    def test_migrate_skips_if_marker_exists(self, tmp_path: Path) -> None:
        """If marker already present, migration is skipped entirely."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        _make_jarvis_home(fake_home)

        cognithor_home = fake_home / ".cognithor"
        cognithor_home.mkdir()
        marker = cognithor_home / ".migrated_from_jarvis"
        marker.write_text("already done")

        with patch("cognithor.__main__.Path") as MockPath:
            MockPath.home.return_value = fake_home
            MockPath.side_effect = Path

            from cognithor.__main__ import _migrate_jarvis_home

            _migrate_jarvis_home()

        # Nothing should be migrated
        assert not (cognithor_home / "memory").exists()

    def test_migrate_skips_if_no_jarvis_dir(self, tmp_path: Path) -> None:
        """If ~/.jarvis/ doesn't exist, nothing happens."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        # No .jarvis directory created

        cognithor_home = fake_home / ".cognithor"
        # Don't create it — migration should handle mkdir

        with patch("cognithor.__main__.Path") as MockPath:
            MockPath.home.return_value = fake_home
            MockPath.side_effect = Path

            from cognithor.__main__ import _migrate_jarvis_home

            _migrate_jarvis_home()

        # No marker, no directories
        marker = cognithor_home / ".migrated_from_jarvis"
        assert not cognithor_home.exists() or not marker.exists()

    def test_migrate_skips_existing_destination_dirs(self, tmp_path: Path) -> None:
        """Dirs that already exist in ~/.cognithor/ are NOT overwritten."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        _make_jarvis_home(fake_home)

        cognithor_home = fake_home / ".cognithor"
        cognithor_home.mkdir()
        # Pre-create memory/ with different content
        (cognithor_home / "memory").mkdir()
        (cognithor_home / "memory" / "existing.txt").write_text("keep me")

        with patch("cognithor.__main__.Path") as MockPath:
            MockPath.home.return_value = fake_home
            MockPath.side_effect = Path

            from cognithor.__main__ import _migrate_jarvis_home

            _migrate_jarvis_home()

        # memory/ should NOT be overwritten
        assert (cognithor_home / "memory" / "existing.txt").read_text() == "keep me"
        assert not (cognithor_home / "memory" / "placeholder.txt").exists()

        # Other dirs should be migrated
        assert (cognithor_home / "data").is_dir()

    def test_migrate_idempotent(self, tmp_path: Path) -> None:
        """Running migration twice is safe (marker prevents re-run)."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        _make_jarvis_home(fake_home)

        cognithor_home = fake_home / ".cognithor"
        cognithor_home.mkdir()

        with patch("cognithor.__main__.Path") as MockPath:
            MockPath.home.return_value = fake_home
            MockPath.side_effect = Path

            from cognithor.__main__ import _migrate_jarvis_home

            _migrate_jarvis_home()
            # Modify a migrated file
            (cognithor_home / "config.yaml").write_text("language: en\n")
            # Run again — should be no-op due to marker
            _migrate_jarvis_home()

        # File should keep the modification (not be overwritten)
        assert (cognithor_home / "config.yaml").read_text() == "language: en\n"
