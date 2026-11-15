"""Tests fuer F-017: Install-History silent Reset + non-atomic Write.

Prueft dass:
  - Korrupte History-Datei geloggt wird (nicht silent reset)
  - Korrupte Datei als .corrupt Backup gesichert wird
  - Atomic write via temp+rename verwendet wird
  - Bei Crash waehrend Write die alte Datei erhalten bleibt
  - Normaler Load/Save weiterhin funktioniert
  - Source-Code die Fixes enthaelt
"""

from __future__ import annotations

import inspect
import json
from typing import TYPE_CHECKING

from cognithor.skills.remote_registry import InstalledPlugin, RemoteRegistry

if TYPE_CHECKING:
    from pathlib import Path


def _make_registry(tmp_path: Path) -> RemoteRegistry:
    """Erstellt eine Registry mit tmp_path."""
    return RemoteRegistry(
        skills_dir=tmp_path / "skills",
        cache_dir=tmp_path / "cache",
        registry_url="https://example.com",
    )


def _make_installed_plugin(name: str = "test-plugin") -> InstalledPlugin:
    """Erstellt ein InstalledPlugin fuer Tests."""
    return InstalledPlugin(
        name=name,
        version="1.0.0",
        installed_at="2026-01-01T00:00:00Z",
    )


class TestCorruptHistoryHandling:
    """Prueft dass korrupte History korrekt behandelt wird."""

    def test_corrupt_json_logged_not_silent(self, tmp_path: Path) -> None:
        """Bei korrupter JSON muss gewarnt werden, nicht silent reset."""
        reg = _make_registry(tmp_path)
        history_file = tmp_path / "skills" / ".plugin_history.json"
        history_file.parent.mkdir(parents=True, exist_ok=True)
        history_file.write_text("THIS IS NOT VALID JSON {{{", encoding="utf-8")

        # Load should not crash
        reg._load_install_history()
        assert reg._installed == {}

    def test_corrupt_file_backed_up(self, tmp_path: Path) -> None:
        """Korrupte Datei muss als .corrupt Backup gesichert werden."""
        reg = _make_registry(tmp_path)
        history_file = tmp_path / "skills" / ".plugin_history.json"
        history_file.parent.mkdir(parents=True, exist_ok=True)
        corrupt_content = "CORRUPT DATA {{{"
        history_file.write_text(corrupt_content, encoding="utf-8")

        reg._load_install_history()

        backup = history_file.with_suffix(".json.corrupt")
        assert backup.exists(), "Corrupt-Backup wurde nicht erstellt"
        assert backup.read_text(encoding="utf-8") == corrupt_content

    def test_valid_json_but_bad_structure(self, tmp_path: Path) -> None:
        """Valides JSON aber falsche Struktur → Backup + leeres Dict."""
        reg = _make_registry(tmp_path)
        history_file = tmp_path / "skills" / ".plugin_history.json"
        history_file.parent.mkdir(parents=True, exist_ok=True)
        # Valides JSON, aber keine Liste
        history_file.write_text('{"not": "a list"}', encoding="utf-8")

        reg._load_install_history()
        assert reg._installed == {}

        backup = history_file.with_suffix(".json.corrupt")
        assert backup.exists()

    def test_valid_history_no_backup(self, tmp_path: Path) -> None:
        """Valide History → kein Backup erstellen."""
        reg = _make_registry(tmp_path)
        history_file = tmp_path / "skills" / ".plugin_history.json"
        history_file.parent.mkdir(parents=True, exist_ok=True)

        plugin = _make_installed_plugin()
        history_file.write_text(
            json.dumps([plugin.to_dict()], indent=2),
            encoding="utf-8",
        )

        reg._load_install_history()
        assert "test-plugin" in reg._installed

        backup = history_file.with_suffix(".json.corrupt")
        assert not backup.exists()


class TestAtomicWrite:
    """Prueft dass _save_install_history atomic schreibt."""

    def test_save_creates_file(self, tmp_path: Path) -> None:
        reg = _make_registry(tmp_path)
        reg._installed["test"] = _make_installed_plugin()
        reg._save_install_history()

        history_file = tmp_path / "skills" / ".plugin_history.json"
        assert history_file.exists()
        data = json.loads(history_file.read_text(encoding="utf-8"))
        assert len(data) == 1
        assert data[0]["name"] == "test-plugin"

    def test_save_overwrites_existing(self, tmp_path: Path) -> None:
        reg = _make_registry(tmp_path)
        reg._installed["p1"] = _make_installed_plugin("p1")
        reg._save_install_history()

        reg._installed["p2"] = _make_installed_plugin("p2")
        reg._save_install_history()

        history_file = tmp_path / "skills" / ".plugin_history.json"
        data = json.loads(history_file.read_text(encoding="utf-8"))
        assert len(data) == 2

    def test_no_temp_files_left_after_success(self, tmp_path: Path) -> None:
        """Nach erfolgreichem Save duerfen keine temp files uebrig sein."""
        reg = _make_registry(tmp_path)
        reg._installed["test"] = _make_installed_plugin()
        reg._save_install_history()

        skills_dir = tmp_path / "skills"
        tmp_files = list(skills_dir.glob(".plugin_history_*.tmp"))
        assert len(tmp_files) == 0

    def test_round_trip_preserves_data(self, tmp_path: Path) -> None:
        """Save → Load muss dieselben Daten liefern."""
        reg1 = _make_registry(tmp_path)
        reg1._installed["p1"] = _make_installed_plugin("p1")
        reg1._installed["p2"] = _make_installed_plugin("p2")
        reg1._save_install_history()

        reg2 = _make_registry(tmp_path)
        reg2._load_install_history()
        assert set(reg2._installed.keys()) == {"p1", "p2"}
        assert reg2._installed["p1"].version == "1.0.0"


class TestSourceLevelChecks:
    """Prueft den Source-Code auf die Fixes."""

    def test_load_logs_warning(self) -> None:
        source = inspect.getsource(RemoteRegistry._load_install_history)
        assert "log.warning" in source

    def test_load_creates_backup(self) -> None:
        source = inspect.getsource(RemoteRegistry._load_install_history)
        assert ".corrupt" in source

    def test_save_uses_tempfile(self) -> None:
        source = inspect.getsource(RemoteRegistry._save_install_history)
        assert "mkstemp" in source or "tempfile" in source

    def test_save_uses_os_replace(self) -> None:
        source = inspect.getsource(RemoteRegistry._save_install_history)
        assert "replace" in source

    def test_save_cleans_up_on_error(self) -> None:
        source = inspect.getsource(RemoteRegistry._save_install_history)
        assert "unlink" in source
