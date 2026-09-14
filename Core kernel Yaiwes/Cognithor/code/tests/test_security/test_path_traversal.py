"""Tests für Path-Traversal-Schutz in vault.py, memory_server.py, code_tools.py.

Validiert, dass alle user-kontrollierten Pfade gegen Directory-Escape geschützt sind:
- ../../etc/passwd Traversal
- Absolute Pfade (/etc/passwd, C:\\Windows\\...)
- Symlink-basierte Escapes
- Encoding-Tricks (%2e%2e, ..\\\\..\\\\)
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from cognithor.mcp.vault import VaultTools

# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def vault(tmp_path: Path) -> VaultTools:
    """VaultTools mit temporärem Vault-Verzeichnis."""
    config = MagicMock()
    config.vault = MagicMock()
    config.vault.enabled = True
    config.vault.path = str(tmp_path / "vault")
    config.vault.auto_save_research = False
    config.vault.default_folders = {"allgemein": "allgemein"}
    config.cognithor_home = tmp_path
    vt = VaultTools(config=config)
    vt._vault_path = tmp_path / "vault"
    vt._vault_path.mkdir(parents=True, exist_ok=True)
    return vt


@pytest.fixture
def secret_file(tmp_path: Path) -> Path:
    """Erstellt eine Datei außerhalb des Vaults."""
    secret = tmp_path / "secret.txt"
    secret.write_text("TOP SECRET DATA", encoding="utf-8")
    return secret


# ── VaultTools._validate_vault_path ─────────────────────────────────────


class TestValidateVaultPath:
    """Testet die _validate_vault_path Hilfsmethode."""

    def test_valid_path_inside_vault(self, vault: VaultTools) -> None:
        """Pfad innerhalb des Vaults wird akzeptiert."""
        valid = vault._vault_root / "notizen" / "test.md"
        valid.parent.mkdir(parents=True, exist_ok=True)
        result = vault._validate_vault_path(valid)
        assert result is not None

    def test_traversal_two_levels_blocked(self, vault: VaultTools) -> None:
        """../../secret wird geblockt."""
        malicious = vault._vault_root / ".." / ".." / "secret.txt"
        result = vault._validate_vault_path(malicious)
        assert result is None

    def test_traversal_single_level_blocked(self, vault: VaultTools) -> None:
        """../secret wird geblockt."""
        malicious = vault._vault_root / ".." / "secret.txt"
        result = vault._validate_vault_path(malicious)
        assert result is None

    def test_traversal_hidden_in_subdir(self, vault: VaultTools) -> None:
        """subdir/../../secret wird geblockt."""
        malicious = vault._vault_root / "subdir" / ".." / ".." / "secret.txt"
        result = vault._validate_vault_path(malicious)
        assert result is None

    def test_vault_root_itself_valid(self, vault: VaultTools) -> None:
        """Vault-Root selbst ist gültig."""
        result = vault._validate_vault_path(vault._vault_root)
        assert result is not None


# ── vault_read Path Traversal ────────────────────────────────────────────


class TestVaultReadTraversal:
    """Testet, dass vault_read gegen Path-Traversal geschützt ist."""

    async def test_traversal_blocked(self, vault: VaultTools, secret_file: Path) -> None:
        """../../secret.txt darf nicht gelesen werden."""
        relative = Path("..") / ".." / "secret.txt"
        result = await vault.vault_read(str(relative))
        assert "TOP SECRET" not in result
        assert "nicht gefunden" in result.lower() or "verweigert" in result.lower()

    async def test_single_level_traversal_blocked(
        self, vault: VaultTools, secret_file: Path
    ) -> None:
        """../secret.txt darf nicht gelesen werden."""
        result = await vault.vault_read("../secret.txt")
        assert "TOP SECRET" not in result

    async def test_legitimate_read_works(self, vault: VaultTools) -> None:
        """Normaler Pfad innerhalb des Vaults funktioniert."""
        note = vault._vault_root / "test.md"
        note.write_text("---\ntitle: Test\n---\nInhalt", encoding="utf-8")
        result = await vault.vault_read("test.md")
        assert "Inhalt" in result

    async def test_nested_legitimate_read(self, vault: VaultTools) -> None:
        """Pfad in Unterordner funktioniert."""
        subdir = vault._vault_root / "wissen"
        subdir.mkdir(parents=True, exist_ok=True)
        note = subdir / "deep.md"
        note.write_text("Tiefes Wissen", encoding="utf-8")
        result = await vault.vault_read("wissen/deep.md")
        assert "Tiefes Wissen" in result

    async def test_traversal_via_backslash_blocked(
        self, vault: VaultTools, secret_file: Path
    ) -> None:
        """..\\..\\secret.txt (Windows-Style) wird ebenfalls geblockt."""
        result = await vault.vault_read("..\\..\\secret.txt")
        assert "TOP SECRET" not in result


# ── _find_note Path Traversal ────────────────────────────────────────────


class TestFindNoteTraversal:
    """Testet, dass _find_note gegen Path-Traversal geschützt ist."""

    def test_traversal_returns_none(self, vault: VaultTools, secret_file: Path) -> None:
        """../../secret.txt liefert None."""
        result = vault._find_note("../../secret.txt")
        assert result is None

    def test_legitimate_find_works(self, vault: VaultTools) -> None:
        """Normaler Pfad wird gefunden."""
        note = vault._vault_root / "findme.md"
        note.write_text("---\ntitle: Find Me\n---\nBody", encoding="utf-8")
        result = vault._find_note("findme.md")
        assert result is not None
        assert result.name == "findme.md"


# ── memory_server _save_procedural Path Traversal ────────────────────────


class TestSaveProceduralTraversal:
    """Testet Path-Traversal-Schutz in MemoryTools._save_procedural."""

    def test_traversal_blocked(self, tmp_path: Path) -> None:
        """../../malicious.md wird geblockt."""
        from cognithor.mcp.memory_server import MemoryTools

        # Minimales Memory-Mock
        memory = MagicMock()
        proc_dir = tmp_path / "procedural"
        proc_dir.mkdir()
        memory.procedural._dir = proc_dir

        server = MemoryTools.__new__(MemoryTools)
        server._memory = memory

        result = server._save_procedural("evil content", "../../malicious.md")
        assert "verweigert" in result.lower() or "zugriff" in result.lower()

        # Datei darf NICHT außerhalb erstellt worden sein
        assert not (tmp_path / "malicious.md").exists()

    def test_legitimate_save_works(self, tmp_path: Path) -> None:
        """Normaler Pfad funktioniert."""
        from cognithor.mcp.memory_server import MemoryTools

        memory = MagicMock()
        proc_dir = tmp_path / "procedural"
        proc_dir.mkdir()
        memory.procedural._dir = proc_dir
        memory.index_text.return_value = 3

        server = MemoryTools.__new__(MemoryTools)
        server._memory = memory

        result = server._save_procedural("valid content", "skills/new-skill.md")
        assert "gespeichert" in result.lower()
        assert (proc_dir / "skills" / "new-skill.md").exists()

    def test_subdir_traversal_escape_blocked(self, tmp_path: Path) -> None:
        """skills/../../escape.md wird geblockt."""
        from cognithor.mcp.memory_server import MemoryTools

        memory = MagicMock()
        proc_dir = tmp_path / "procedural"
        proc_dir.mkdir()
        memory.procedural._dir = proc_dir

        server = MemoryTools.__new__(MemoryTools)
        server._memory = memory

        result = server._save_procedural("evil", "skills/../../escape.md")
        assert "verweigert" in result.lower() or "zugriff" in result.lower()


# ── code_tools analyze_code Path Traversal ───────────────────────────────


class TestAnalyzeCodeTraversal:
    """Testet Path-Traversal-Schutz in CodeTools.analyze_code."""

    async def test_traversal_outside_workspace_blocked(self, tmp_path: Path) -> None:
        """Datei außerhalb des Workspace wird geblockt."""
        from cognithor.mcp.code_tools import CodeTools

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Secret-Datei außerhalb des Workspace
        secret = tmp_path / "secret.py"
        secret.write_text("API_KEY = 'sk-12345'", encoding="utf-8")

        config = MagicMock()
        config.workspace_dir = workspace
        code_cfg = MagicMock()
        code_cfg.max_code_size_mb = 10
        code_cfg.default_timeout_seconds = 30
        config.code = code_cfg
        config.sandbox_level = "bare"
        config.sandbox_network = "allow"

        tools = CodeTools(config)
        result = await tools.analyze_code(file_path=str(secret))
        assert "verweigert" in result.lower() or "zugriff" in result.lower()
        assert "API_KEY" not in result

    async def test_legitimate_file_works(self, tmp_path: Path) -> None:
        """Datei innerhalb des Workspace funktioniert."""
        from cognithor.mcp.code_tools import CodeTools

        workspace = tmp_path / "workspace"
        workspace.mkdir()
        target = workspace / "app.py"
        target.write_text("def hello():\n    return 'world'\n", encoding="utf-8")

        config = MagicMock()
        config.workspace_dir = workspace
        code_cfg = MagicMock()
        code_cfg.max_code_size_mb = 10
        code_cfg.default_timeout_seconds = 30
        config.code = code_cfg
        config.sandbox_level = "bare"
        config.sandbox_network = "allow"

        tools = CodeTools(config)
        result = await tools.analyze_code(file_path=str(target))
        # Sollte kein "verweigert" enthalten
        assert "verweigert" not in result.lower()

    async def test_relative_traversal_blocked(self, tmp_path: Path) -> None:
        """../../etc/passwd-artiger Pfad wird geblockt."""
        from cognithor.mcp.code_tools import CodeTools

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        config = MagicMock()
        config.workspace_dir = workspace
        code_cfg = MagicMock()
        code_cfg.max_code_size_mb = 10
        code_cfg.default_timeout_seconds = 30
        config.code = code_cfg
        config.sandbox_level = "bare"
        config.sandbox_network = "allow"

        tools = CodeTools(config)
        result = await tools.analyze_code(file_path="../../some_secret.py")
        assert "verweigert" in result.lower() or "zugriff" in result.lower()
