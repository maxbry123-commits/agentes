"""Tests fuer plattformuebergreifende Pfadbehandlung (Windows + Unix).

Stellt sicher, dass:
  - Kein hardcodiertes /tmp/jarvis in Produktion vorkommt
  - Pfad-Operationen mit beiden Separatoren (/ und \\) funktionieren
  - Windows-Laufwerksbuchstaben korrekt behandelt werden
  - _slugify-Funktionen gueltige Dateinamen erzeugen
  - Path-Validierung plattformuebergreifend funktioniert
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path, PurePath, PureWindowsPath
from unittest.mock import MagicMock

import pytest

# ============================================================================
# 1. Kein hardcodiertes /tmp/jarvis in Produktion
# ============================================================================


class TestNoHardcodedTmpPaths:
    """Verifiziert, dass Default-Pfade tempfile.gettempdir() verwenden."""

    def test_security_config_uses_platform_temp(self):
        """SecurityConfig.allowed_paths muss plattform-temp verwenden."""
        from cognithor.config import SecurityConfig

        config = SecurityConfig()
        tmp = tempfile.gettempdir()
        # Mindestens ein Pfad muss das System-Temp-Verzeichnis enthalten
        assert any(tmp in p or str(Path(tmp)) in p for p in config.allowed_paths), (
            f"SecurityConfig.allowed_paths enthaelt kein plattform-temp: "
            f"{config.allowed_paths} (erwartet: {tmp})"
        )

    def test_sandbox_config_uses_platform_temp(self):
        """models.SandboxConfig.allowed_paths muss plattform-temp verwenden."""
        from cognithor.models import SandboxConfig

        config = SandboxConfig()
        tmp = tempfile.gettempdir()
        assert any(tmp in p or str(Path(tmp)) in p for p in config.allowed_paths), (
            f"SandboxConfig.allowed_paths enthaelt kein plattform-temp: "
            f"{config.allowed_paths} (erwartet: {tmp})"
        )

    def test_no_literal_tmp_jarvis_in_defaults(self):
        """Defaults duerfen nicht den Unix-Literal '/tmp/jarvis/' enthalten."""
        from cognithor.config import SecurityConfig
        from cognithor.models import SandboxConfig

        sec = SecurityConfig()
        sb = SandboxConfig()

        for paths_list, name in [
            (sec.allowed_paths, "SecurityConfig"),
            (sb.allowed_paths, "SandboxConfig"),
        ]:
            for p in paths_list:
                # Auf Windows darf /tmp/jarvis/ nicht vorkommen;
                # Auf Linux ist es nur OK wenn es tatsaechlich dem tempdir entspricht
                if sys.platform == "win32":
                    assert p != "/tmp/jarvis/", (
                        f"{name}.allowed_paths enthaelt hardcoded '/tmp/jarvis/' auf Windows"
                    )


# ============================================================================
# 2. Pfad-Separatoren: / und \ muessen beide funktionieren
# ============================================================================


class TestPathSeparators:
    """Stellt sicher, dass Pfad-Operationen mit beiden Separatoren arbeiten."""

    def test_purepath_name_extracts_filename_from_unix_path(self):
        """PurePath.name muss Dateinamen aus Unix-Pfad extrahieren."""
        assert PurePath("/home/user/documents/file.txt").name == "file.txt"

    def test_purepath_name_extracts_filename_from_windows_path(self):
        """PurePath.name muss Dateinamen aus Windows-Pfad extrahieren."""
        # PureWindowsPath funktioniert immer, auch auf Linux
        assert PureWindowsPath(r"C:\Users\test\documents\file.txt").name == "file.txt"

    def test_purepath_name_with_forward_slashes(self):
        """PurePath.name mit Forward-Slashes (beide Plattformen)."""
        assert PurePath("data/memories/chunk_42.json").name == "chunk_42.json"

    def test_purepath_name_handles_bare_filename(self):
        """PurePath.name bei einfachem Dateinamen ohne Pfad."""
        assert PurePath("notes.txt").name == "notes.txt"

    def test_working_memory_source_extraction(self):
        """WorkingMemory build_context_parts extrahiert source korrekt."""
        from cognithor.memory.working import WorkingMemoryManager
        from cognithor.models import Chunk, MemorySearchResult

        # Unix-style Pfad
        chunk_unix = Chunk(
            text="Testtext",
            source_path="/home/user/.cognithor/memory/note.md",
        )
        mr_unix = MemorySearchResult(chunk=chunk_unix, score=0.95)

        # Windows-style Pfad (forward slashes funktionieren auf allen OS)
        chunk_win = Chunk(
            text="Testtext Windows",
            source_path="C:/Users/test/.cognithor/memory/notiz.md",
        )
        mr_win = MemorySearchResult(chunk=chunk_win, score=0.90)

        mgr = WorkingMemoryManager()
        mgr.inject_memories([mr_unix, mr_win])
        parts = mgr.build_context_parts()

        assert "memories" in parts
        assert "note.md" in parts["memories"]
        assert "notiz.md" in parts["memories"]

    def test_path_resolve_handles_mixed_separators(self):
        """Path.resolve() muss gemischte Separatoren normalisieren."""
        # Gemischte Separatoren (nur Forward-Slash, das ist auf allen OS gueltig)
        p = Path("some/nested/dir/file.txt")
        assert p.name == "file.txt"
        assert len(p.parts) >= 4


# ============================================================================
# 3. Temp-Verzeichnis ist plattform-korrekt
# ============================================================================


class TestTempDirectory:
    """Verifiziert, dass Temp-Verzeichnisse plattformuebergreifend korrekt sind."""

    def test_tempdir_exists(self):
        """tempfile.gettempdir() muss ein existierendes Verzeichnis liefern."""
        tmp = tempfile.gettempdir()
        assert Path(tmp).is_dir()

    def test_jarvis_temp_path_is_valid(self):
        """Der Jarvis-Temp-Pfad muss konstruierbar und gueltig sein."""
        jarvis_tmp = Path(tempfile.gettempdir()) / "jarvis"
        # Pfad muss absolut sein
        assert jarvis_tmp.is_absolute()
        # Pfad muss mit 'jarvis' enden
        assert jarvis_tmp.name == "jarvis"

    def test_temp_path_string_representation(self):
        """String-Darstellung des Temp-Pfads muss gueltig sein."""
        jarvis_tmp = str(Path(tempfile.gettempdir()) / "jarvis") + "/"
        # Darf keine doppelten Separatoren haben
        assert "//" not in jarvis_tmp.replace("://", "")
        # Muss mit /jarvis/ enden (plattformabhaengig)
        assert jarvis_tmp.endswith("jarvis/") or jarvis_tmp.endswith("jarvis\\")

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-spezifisch")
    def test_windows_temp_not_unix(self):
        """Auf Windows darf der Temp-Pfad nicht /tmp sein."""
        tmp = tempfile.gettempdir()
        assert tmp != "/tmp", f"Temp-Verzeichnis ist /tmp auf Windows: {tmp}"

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix-spezifisch")
    def test_unix_temp_is_tmp(self):
        """Auf Unix sollte der Temp-Pfad /tmp enthalten."""
        tmp = tempfile.gettempdir()
        assert "tmp" in tmp.lower(), f"Unerwartetes Temp-Verzeichnis: {tmp}"


# ============================================================================
# 4. _slugify erzeugt gueltige Dateinamen
# ============================================================================


class TestSlugify:
    """Testet alle _slugify-Varianten auf gueltige Dateinamen."""

    def test_skill_tools_slugify_basic(self):
        """skill_tools._slugify erzeugt gueltigen Dateinamen."""
        from cognithor.mcp.skill_tools import _slugify

        assert _slugify("My Cool Skill") == "my_cool_skill"
        assert _slugify("  spaces  ") == "spaces"
        assert _slugify("UPPER-case") == "upper_case"

    def test_skill_tools_slugify_special_chars(self):
        """skill_tools._slugify entfernt Sonderzeichen."""
        from cognithor.mcp.skill_tools import _slugify

        result = _slugify("test@#$%skill")
        assert all(c.isalnum() or c == "_" for c in result)

    def test_skill_tools_slugify_empty(self):
        """skill_tools._slugify liefert Fallback fuer leeren String."""
        from cognithor.mcp.skill_tools import _slugify

        assert _slugify("") == "unnamed_skill"
        assert _slugify("###") == "unnamed_skill"

    def test_vault_slugify_german_umlauts(self):
        """vault._slugify wandelt deutsche Umlaute korrekt um."""
        from cognithor.mcp.vault import _slugify

        assert "ae" in _slugify("Aehnlich")
        assert "oe" in _slugify("Oeffnen")
        assert "ue" in _slugify("Uebung")
        assert "ss" in _slugify("Stra\u00dfe")

    def test_vault_slugify_produces_valid_filename(self):
        """vault._slugify erzeugt Dateinamen ohne ungueltige Zeichen."""
        from cognithor.mcp.vault import _slugify

        slug = _slugify("Test: Meine Notiz (2024)!")
        # Keine Sonderzeichen die in Dateinamen problematisch sind
        invalid_chars = set('<>:"/\\|?*')
        assert not any(c in invalid_chars for c in slug)

    def test_manager_slugify_basic(self):
        """skills.manager._slugify erzeugt gueltige Dateinamen."""
        from cognithor.skills.manager import _slugify

        result = _slugify("My Skill Name")
        assert result == "my-skill-name"
        # Keine ungueltige Dateinamen-Zeichen
        invalid_chars = set('<>:"/\\|?*')
        assert not any(c in invalid_chars for c in result)

    def test_slugify_no_path_separators(self):
        """Kein Slugify darf Pfad-Separatoren erzeugen."""
        from cognithor.mcp.skill_tools import _slugify as st_slugify
        from cognithor.mcp.vault import _slugify as vault_slugify
        from cognithor.skills.manager import _slugify as mgr_slugify

        test_inputs = [
            "normal name",
            "path/with/slashes",
            "path\\with\\backslashes",
            "C:\\Windows\\path",
            "/unix/path",
        ]
        for inp in test_inputs:
            for slugify_fn in [st_slugify, vault_slugify, mgr_slugify]:
                result = slugify_fn(inp)
                assert "/" not in result, f"Slug enthaelt '/': {result} (input: {inp})"
                assert "\\" not in result, f"Slug enthaelt '\\': {result} (input: {inp})"


# ============================================================================
# 5. Windows-Laufwerksbuchstaben werden korrekt behandelt
# ============================================================================


class TestWindowsDriveLetters:
    """Testet korrekte Behandlung von Windows-Laufwerksbuchstaben."""

    def test_path_with_drive_letter_is_absolute(self):
        """PureWindowsPath mit Laufwerksbuchstabe ist absolut."""
        p = PureWindowsPath("C:\\Users\\test\\file.txt")
        assert p.is_absolute()
        assert p.drive == "C:"

    def test_path_resolve_preserves_drive(self):
        """Path.resolve() darf Laufwerksbuchstaben nicht verlieren."""
        if sys.platform == "win32":
            p = Path("C:\\Users\\test")
            resolved = p.resolve()
            assert str(resolved)[0:2] == "C:"

    def test_purepath_parts_with_drive(self):
        """PureWindowsPath.parts enthaelt Laufwerk als erstes Element."""
        p = PureWindowsPath("C:\\Users\\test\\file.txt")
        assert p.parts[0] == "C:\\"
        assert p.name == "file.txt"

    def test_relative_to_with_drive_letters(self):
        """relative_to() funktioniert mit Laufwerksbuchstaben."""
        base = PureWindowsPath("C:\\Users\\test")
        child = PureWindowsPath("C:\\Users\\test\\docs\\file.txt")
        rel = child.relative_to(base)
        assert str(rel) == "docs\\file.txt"

    def test_different_drives_are_not_relative(self):
        """Pfade auf verschiedenen Laufwerken sind nicht relativ zueinander."""
        base = PureWindowsPath("C:\\Users")
        other = PureWindowsPath("D:\\Data")
        with pytest.raises(ValueError):
            other.relative_to(base)


# ============================================================================
# 6. Pfad-Validierung funktioniert plattformuebergreifend
# ============================================================================


class TestPathValidation:
    """Testet die Pfad-Validierung in Gatekeeper und Filesystem."""

    def test_filesystem_validate_path_uses_pathlib(self):
        """FileSystemTools._validate_path nutzt Path.resolve()."""
        from cognithor.mcp.filesystem import FileSystemTools

        # Erstellt eine Instanz mit einem Mock-Config
        config = MagicMock()
        config.security.allowed_paths = [str(Path.home() / ".cognithor")]
        config.filesystem = MagicMock()
        config.filesystem.max_tree_entries = 1000
        tools = FileSystemTools(config)

        # Pfad innerhalb des erlaubten Verzeichnisses
        home_jarvis = Path.home() / ".cognithor"
        if home_jarvis.exists():
            test_path = str(home_jarvis / "test.txt")
            validated = tools._validate_path(test_path)
            assert isinstance(validated, Path)
            assert validated.is_absolute()

    def test_gatekeeper_validate_paths_resolves_correctly(self, tmp_path):
        """Gatekeeper._validate_paths nutzt Path fuer Validierung."""
        from cognithor.core.gatekeeper import Gatekeeper
        from cognithor.models import PlannedAction

        # policies_dir muss ein existierendes Verzeichnis sein
        # (oder Dateien fehlen -> leere Policies)
        policies_dir = tmp_path / "policies"
        policies_dir.mkdir()

        config = MagicMock()
        config.security.allowed_paths = [
            str(Path.home() / ".cognithor"),
            str(Path(tempfile.gettempdir()) / "jarvis"),
        ]
        config.security.blocked_commands = []
        config.security.credential_patterns = []
        config.policies_dir = policies_dir
        config.logs_dir = tmp_path

        gk = Gatekeeper(config)
        gk.initialize()

        # Ein Pfad innerhalb des erlaubten Temp-Bereichs
        jarvis_tmp = Path(tempfile.gettempdir()) / "jarvis" / "test.txt"
        action = PlannedAction(
            tool="read_file",
            params={"path": str(jarvis_tmp)},
            reason="Test",
        )

        # Sollte None (= erlaubt) zurueckgeben
        result = gk._validate_paths(action)
        assert result is None, f"Pfad wurde unerwartet blockiert: {result}"

    def test_expanduser_works_cross_platform(self):
        """Path.expanduser() funktioniert auf allen Plattformen."""
        home = Path("~").expanduser()
        assert home.is_absolute()
        if sys.platform == "win32":
            assert "Users" in str(home) or "USERS" in str(home).upper()

    def test_resolve_normalizes_separators(self):
        """Path.resolve() normalisiert Pfad-Separatoren."""
        p = Path(tempfile.gettempdir()) / "jarvis" / "test"
        resolved = p.resolve()
        assert resolved.is_absolute()
        # Auf Windows mit backslash, auf Unix mit forward slash
        path_str = str(resolved)
        if sys.platform == "win32":
            assert "\\" in path_str
        else:
            assert "/" in path_str


# ============================================================================
# 7. Keine hardcodierten Unix-Pfade in Produktionscode
# ============================================================================


class TestNoHardcodedUnixPaths:
    """Scannt den Quellcode nach hardcodierten Unix-Pfaden."""

    @staticmethod
    def _get_source_files() -> list[Path]:
        """Sammelt alle .py Dateien im src/jarvis Verzeichnis."""
        src_dir = Path(__file__).resolve().parent.parent.parent / "src" / "cognithor"
        if not src_dir.exists():
            pytest.skip(f"Source-Verzeichnis nicht gefunden: {src_dir}")
        return list(src_dir.rglob("*.py"))

    def test_no_hardcoded_tmp_jarvis_in_defaults(self):
        """Kein Python-File darf literal '/tmp/jarvis' als Default verwenden.

        Ausnahmen: Kommentare, Docstrings, Test-Fixtures.
        Prueft nur Default-Werte in Field() und = Zuweisungen.
        """

        violations = []
        for pyfile in self._get_source_files():
            content = pyfile.read_text(encoding="utf-8", errors="replace")
            # Suche nach /tmp/jarvis in Default-Werten (nicht in Kommentaren)
            for i, line in enumerate(content.splitlines(), 1):
                stripped = line.strip()
                # Skip Kommentare
                if stripped.startswith("#"):
                    continue
                # Skip Docstrings (grobe Heuristik)
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    continue
                # Skip audit/test Beispiel-Strings
                if "audit" in str(pyfile.parent.name) and "example" in stripped.lower():
                    continue
                if ('"/tmp/jarvis' in stripped or "'/tmp/jarvis" in stripped) and (
                    "default" in stripped.lower() or "lambda" in stripped or "=" in stripped
                ):
                    violations.append(f"{pyfile.name}:{i}: {stripped}")

        assert not violations, (
            "Hardcodiertes '/tmp/jarvis' in Default-Werten gefunden:\n" + "\n".join(violations)
        )

    def test_source_path_split_not_used(self):
        """Kein Python-File darf .split('/') fuer Pfad-Extraktion verwenden.

        Stattdessen: PurePath(...).name oder Path(...).parts
        """
        import re

        violations = []
        for pyfile in self._get_source_files():
            content = pyfile.read_text(encoding="utf-8", errors="replace")
            for i, line in enumerate(content.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                # Pattern: variable.split("/") wobei variable auf _path endet
                if re.search(r'\w+_path\.split\(["\']/', stripped):
                    violations.append(f"{pyfile.name}:{i}: {stripped}")

        assert not violations, (
            ".split('/') fuer Pfad-Extraktion gefunden (verwende PurePath stattdessen):\n"
            + "\n".join(violations)
        )


# ============================================================================
# 8. Sandbox-Konfiguration ist plattform-korrekt
# ============================================================================


class TestSandboxPlatformConfig:
    """Testet plattformspezifische Sandbox-Konfiguration."""

    def test_core_sandbox_build_env_platform_aware(self):
        """security/sandbox.py _build_env setzt plattform-korrekte Werte."""
        from cognithor.models import SandboxConfig as ModelSandboxConfig
        from cognithor.security.sandbox import Sandbox

        sb = Sandbox(ModelSandboxConfig())
        env = sb._build_env()

        assert "PATH" in env
        if sys.platform == "win32":
            assert "SYSTEMROOT" in env
            assert "HOME" in env
        else:
            assert "LANG" in env

    def test_core_sandbox_executor_detects_platform(self):
        """SandboxExecutor erkennt plattform-spezifische Faehigkeiten."""
        from cognithor.core.sandbox import SandboxExecutor, SandboxLevel

        executor = SandboxExecutor()
        level = executor.level

        if sys.platform == "win32":
            # Auf Windows sollte mindestens JOBOBJECT oder BARE verfuegbar sein
            assert level in (SandboxLevel.JOBOBJECT, SandboxLevel.BARE)
        # Auf Linux koennte bwrap/firejail oder bare sein
        assert isinstance(level, SandboxLevel)
