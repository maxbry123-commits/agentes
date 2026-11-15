"""Tests fuer F-016: shutil.rmtree ohne Path-Traversal-Validation.

Prueft dass:
  - skill_name mit '../' in install() abgelehnt wird
  - skill_name mit '../' in uninstall() abgelehnt wird
  - skill_name mit absoluten Pfaden abgelehnt wird
  - Normale Skill-Namen weiterhin funktionieren
  - Path-Traversal nicht zu Dateiloeschung fuehrt
  - resolve() + relative_to() Pattern im Source vorhanden ist
"""

from __future__ import annotations

import inspect
import os
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest

from cognithor.skills.community.client import CommunityRegistryClient, RegistryEntry
from cognithor.skills.community.validator import ValidationResult

if TYPE_CHECKING:
    from pathlib import Path


def _make_client(tmp_path: Path) -> CommunityRegistryClient:
    """Erstellt einen Client mit tmp_path als community_dir."""
    return CommunityRegistryClient(community_dir=tmp_path / "community")


def _populate_registry(client: CommunityRegistryClient, skill_name: str) -> None:
    """Fuegt einen Fake-Entry in den Registry-Cache ein."""
    client._registry_cache[skill_name] = RegistryEntry(
        name=skill_name,
        version="1.0",
        description="test",
        content_hash="",  # Kein Hash-Check
    )


class TestInstallPathTraversal:
    """Prueft Path-Traversal-Schutz in install()."""

    @pytest.mark.asyncio
    async def test_dotdot_rejected(self, tmp_path: Path) -> None:
        client = _make_client(tmp_path)
        _populate_registry(client, "../../evil")

        with patch.object(client, "_fetch_text", new_callable=AsyncMock, return_value="# Evil"):
            with patch.object(
                client._validator,
                "validate",
                return_value=ValidationResult(valid=True),
            ):
                result = await client.install("../../evil")

        assert not result.success
        assert any("Path-Traversal" in e for e in result.errors)

    @pytest.mark.asyncio
    async def test_dotdot_nested_rejected(self, tmp_path: Path) -> None:
        client = _make_client(tmp_path)
        _populate_registry(client, "foo/../../bar")

        with patch.object(client, "_fetch_text", new_callable=AsyncMock, return_value="# Test"):
            with patch.object(
                client._validator,
                "validate",
                return_value=ValidationResult(valid=True),
            ):
                result = await client.install("foo/../../bar")

        assert not result.success
        assert any("Path-Traversal" in e for e in result.errors)

    @pytest.mark.asyncio
    async def test_normal_name_accepted(self, tmp_path: Path) -> None:
        client = _make_client(tmp_path)
        _populate_registry(client, "my-cool-skill")

        with patch.object(client, "_fetch_text", new_callable=AsyncMock, return_value="# Skill"):
            with patch.object(
                client._validator,
                "validate",
                return_value=ValidationResult(valid=True),
            ):
                result = await client.install("my-cool-skill")

        assert result.success
        assert (tmp_path / "community" / "my-cool-skill" / "skill.md").exists()

    @pytest.mark.asyncio
    async def test_traversal_does_not_create_dirs(self, tmp_path: Path) -> None:
        """Path-Traversal darf keine Verzeichnisse ausserhalb erstellen."""
        client = _make_client(tmp_path)
        _populate_registry(client, "../escape")

        target = tmp_path / "escape"
        assert not target.exists()

        with patch.object(client, "_fetch_text", new_callable=AsyncMock, return_value="# Evil"):
            with patch.object(
                client._validator,
                "validate",
                return_value=ValidationResult(valid=True),
            ):
                result = await client.install("../escape")

        assert not result.success
        assert not target.exists()


class TestUninstallPathTraversal:
    """Prueft Path-Traversal-Schutz in uninstall()."""

    @pytest.mark.asyncio
    async def test_dotdot_rejected(self, tmp_path: Path) -> None:
        client = _make_client(tmp_path)
        result = await client.uninstall("../../evil")
        assert result is False

    @pytest.mark.asyncio
    async def test_dotdot_does_not_delete(self, tmp_path: Path) -> None:
        """Path-Traversal darf keine Verzeichnisse ausserhalb loeschen."""
        # Erstelle ein Verzeichnis ausserhalb von community_dir
        target = tmp_path / "important_data"
        target.mkdir()
        (target / "file.txt").write_text("important")

        client = _make_client(tmp_path)
        # Berechne den relativen Traversal-Pfad
        result = await client.uninstall("../../important_data")

        assert result is False
        # Das Verzeichnis muss noch existieren
        assert target.exists()
        assert (target / "file.txt").read_text() == "important"

    @pytest.mark.asyncio
    async def test_normal_uninstall_works(self, tmp_path: Path) -> None:
        """Normaler Skill-Name wird korrekt deinstalliert."""
        client = _make_client(tmp_path)
        skill_dir = tmp_path / "community" / "test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "skill.md").write_text("# Test")

        result = await client.uninstall("test-skill")

        assert result is True
        assert not skill_dir.exists()

    @pytest.mark.asyncio
    async def test_nonexistent_skill_returns_false(self, tmp_path: Path) -> None:
        client = _make_client(tmp_path)
        (tmp_path / "community").mkdir(parents=True, exist_ok=True)
        result = await client.uninstall("nonexistent")
        assert result is False


class TestEdgeCases:
    """Prueft Grenzfaelle."""

    @pytest.mark.asyncio
    async def test_skill_name_with_backslash(self, tmp_path: Path) -> None:
        """Backslash-basierte Traversal (Windows)."""
        client = _make_client(tmp_path)
        _populate_registry(client, "..\\..\\evil")

        with patch.object(client, "_fetch_text", new_callable=AsyncMock, return_value="# Evil"):
            with patch.object(
                client._validator,
                "validate",
                return_value=ValidationResult(valid=True),
            ):
                result = await client.install("..\\..\\evil")

        # Auf Windows resolved Path() backslashes korrekt
        # Der Test prueft dass es nicht ausserhalb landet
        if os.sep == "\\":
            # Auf Windows: resolve() behandelt Backslashes korrekt
            assert not result.success or "community" in result.install_path
        else:
            # Auf Linux: Backslash ist ein gueltiger Dateiname-Zeichen
            # Der Name "..\\..\\evil" wird literal verwendet
            pass  # Kein Path-Traversal auf Linux

    @pytest.mark.asyncio
    async def test_skill_name_only_dots(self, tmp_path: Path) -> None:
        """Skill-Name '..' allein ist Path-Traversal."""
        client = _make_client(tmp_path)
        _populate_registry(client, "..")

        with patch.object(client, "_fetch_text", new_callable=AsyncMock, return_value="# Evil"):
            with patch.object(
                client._validator,
                "validate",
                return_value=ValidationResult(valid=True),
            ):
                result = await client.install("..")

        assert not result.success


class TestSourceLevelChecks:
    """Prueft den Source-Code auf Path-Traversal-Schutz."""

    def test_install_uses_resolve(self) -> None:
        source = inspect.getsource(CommunityRegistryClient.install)
        assert ".resolve()" in source

    def test_install_uses_relative_to(self) -> None:
        source = inspect.getsource(CommunityRegistryClient.install)
        assert ".relative_to(" in source

    def test_uninstall_uses_resolve(self) -> None:
        source = inspect.getsource(CommunityRegistryClient.uninstall)
        assert ".resolve()" in source

    def test_uninstall_uses_relative_to(self) -> None:
        source = inspect.getsource(CommunityRegistryClient.uninstall)
        assert ".relative_to(" in source
