"""Tests for the Remote Plugin Registry.

Covers manifest handling, install/update/rollback, dependency resolution,
search, checksum verification, and edge cases.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from cognithor.skills.remote_registry import (
    DependencyResolver,
    InstalledPlugin,
    InstallResult,
    InstallStatus,
    PluginManifest,
    RemoteRegistry,
)

if TYPE_CHECKING:
    from pathlib import Path

# ============================================================================
# PluginManifest
# ============================================================================


class TestPluginManifest:
    def test_defaults(self) -> None:
        m = PluginManifest(name="test", version="1.0.0")
        assert m.license == "MIT"
        assert m.dependencies == []
        assert m.is_signed is False

    def test_round_trip(self) -> None:
        m = PluginManifest(
            name="weather",
            version="2.0.0",
            description="Weather skill",
            author="Test",
            tags=["weather", "forecast"],
            dependencies=["http-client"],
        )
        d = m.to_dict()
        m2 = PluginManifest.from_dict(d)
        assert m2.name == "weather"
        assert m2.version == "2.0.0"
        assert m2.tags == ["weather", "forecast"]
        assert m2.dependencies == ["http-client"]

    def test_is_signed(self) -> None:
        m = PluginManifest(name="t", version="1.0", signature="abc123")
        assert m.is_signed is True

    def test_verify_checksum_valid(self) -> None:
        import hashlib

        content = b"hello world"
        checksum = hashlib.sha256(content).hexdigest()
        m = PluginManifest(name="t", version="1.0", checksum=checksum)
        assert m.verify_checksum(content) is True

    def test_verify_checksum_invalid(self) -> None:
        m = PluginManifest(name="t", version="1.0", checksum="wrong")
        assert m.verify_checksum(b"hello") is False

    def test_verify_checksum_empty(self) -> None:
        m = PluginManifest(name="t", version="1.0")
        assert m.verify_checksum(b"anything") is True  # No checksum = always valid


# ============================================================================
# InstalledPlugin
# ============================================================================


class TestInstalledPlugin:
    def test_round_trip(self) -> None:
        p = InstalledPlugin(name="test", version="1.0", source="remote", previous_versions=["0.9"])
        d = p.to_dict()
        p2 = InstalledPlugin.from_dict(d)
        assert p2.name == "test"
        assert p2.version == "1.0"
        assert p2.previous_versions == ["0.9"]


# ============================================================================
# InstallResult
# ============================================================================


class TestInstallResult:
    def test_success(self) -> None:
        r = InstallResult(plugin="x", version="1.0", status=InstallStatus.INSTALLED)
        assert r.success is True

    def test_failure(self) -> None:
        r = InstallResult(plugin="x", version="", status=InstallStatus.FAILED)
        assert r.success is False

    def test_to_dict(self) -> None:
        r = InstallResult(
            plugin="x", version="1.0", status=InstallStatus.INSTALLED, warnings=["unsigned"]
        )
        d = r.to_dict()
        assert d["success"] is True
        assert d["warnings"] == ["unsigned"]


# ============================================================================
# DependencyResolver
# ============================================================================


class TestDependencyResolver:
    def test_no_dependencies(self) -> None:
        resolver = DependencyResolver()
        resolver.set_available([PluginManifest(name="a", version="1.0")])
        order = resolver.resolve("a")
        assert order == ["a"]

    def test_linear_dependencies(self) -> None:
        resolver = DependencyResolver()
        resolver.set_available(
            [
                PluginManifest(name="a", version="1.0", dependencies=["b"]),
                PluginManifest(name="b", version="1.0", dependencies=["c"]),
                PluginManifest(name="c", version="1.0"),
            ]
        )
        order = resolver.resolve("a")
        assert order == ["c", "b", "a"]

    def test_diamond_dependencies(self) -> None:
        resolver = DependencyResolver()
        resolver.set_available(
            [
                PluginManifest(name="a", version="1.0", dependencies=["b", "c"]),
                PluginManifest(name="b", version="1.0", dependencies=["d"]),
                PluginManifest(name="c", version="1.0", dependencies=["d"]),
                PluginManifest(name="d", version="1.0"),
            ]
        )
        order = resolver.resolve("a")
        assert order.index("d") < order.index("b")
        assert order.index("d") < order.index("c")
        assert order[-1] == "a"

    def test_circular_dependency(self) -> None:
        resolver = DependencyResolver()
        resolver.set_available(
            [
                PluginManifest(name="a", version="1.0", dependencies=["b"]),
                PluginManifest(name="b", version="1.0", dependencies=["a"]),
            ]
        )
        with pytest.raises(ValueError, match="Circular"):
            resolver.resolve("a")

    def test_find_missing(self) -> None:
        resolver = DependencyResolver()
        resolver.set_available(
            [
                PluginManifest(name="a", version="1.0", dependencies=["b", "c"]),
                PluginManifest(name="b", version="1.0"),
                PluginManifest(name="c", version="1.0"),
            ]
        )
        missing = resolver.find_missing("a", installed={"b"})
        assert missing == ["c"]

    def test_unknown_plugin(self) -> None:
        resolver = DependencyResolver()
        order = resolver.resolve("unknown")
        assert order == ["unknown"]


# ============================================================================
# RemoteRegistry — Install
# ============================================================================


class TestRemoteRegistryInstall:
    def _make_registry(self, tmp_path: Path) -> RemoteRegistry:
        skills = tmp_path / "skills"
        reg = RemoteRegistry(skills)
        reg.register_remote(
            PluginManifest(
                name="weather",
                version="1.0.0",
                description="Weather forecast skill",
                tags=["weather"],
            )
        )
        reg.register_remote(
            PluginManifest(
                name="calendar",
                version="2.0.0",
                description="Calendar management",
                category="productivity",
                tags=["calendar", "schedule"],
            )
        )
        return reg

    def test_install_plugin(self, tmp_path: Path) -> None:
        reg = self._make_registry(tmp_path)
        result = reg.install("weather", content="Weather skill content")
        assert result.status == InstallStatus.INSTALLED
        assert result.success

    def test_install_unknown_plugin(self, tmp_path: Path) -> None:
        reg = self._make_registry(tmp_path)
        result = reg.install("nonexistent")
        assert result.status == InstallStatus.FAILED
        assert "not found" in result.message

    def test_install_already_installed(self, tmp_path: Path) -> None:
        reg = self._make_registry(tmp_path)
        reg.install("weather")
        result = reg.install("weather")
        assert result.status == InstallStatus.INSTALLED
        assert "Already installed" in result.message

    def test_install_unsigned_warning(self, tmp_path: Path) -> None:
        reg = self._make_registry(tmp_path)
        result = reg.install("weather", verify_signature=True)
        assert any("not signed" in w for w in result.warnings)

    def test_install_checksum_failure(self, tmp_path: Path) -> None:
        reg = RemoteRegistry(tmp_path / "skills")
        reg.register_remote(
            PluginManifest(
                name="bad",
                version="1.0",
                checksum="wrong_checksum",
            )
        )
        result = reg.install("bad", content="some content")
        assert result.status == InstallStatus.FAILED
        assert "Checksum" in result.message

    def test_install_creates_files(self, tmp_path: Path) -> None:
        reg = self._make_registry(tmp_path)
        reg.install("weather", content="test content")
        skill_file = tmp_path / "skills" / "weather" / "skill.md"
        manifest_file = tmp_path / "skills" / "weather" / "manifest.json"
        assert skill_file.exists()
        assert manifest_file.exists()


# ============================================================================
# RemoteRegistry — Update & Rollback
# ============================================================================


class TestRemoteRegistryUpdateRollback:
    def test_update_plugin(self, tmp_path: Path) -> None:
        reg = RemoteRegistry(tmp_path / "skills")
        reg.register_remote(PluginManifest(name="p", version="1.0"))
        reg.install("p")
        # Simulate new version
        reg.register_remote(PluginManifest(name="p", version="2.0"))
        result = reg.update("p")
        assert result.status == InstallStatus.INSTALLED
        assert reg.get_installed("p").version == "2.0"

    def test_update_not_installed(self, tmp_path: Path) -> None:
        reg = RemoteRegistry(tmp_path / "skills")
        result = reg.update("missing")
        assert result.status == InstallStatus.FAILED

    def test_rollback(self, tmp_path: Path) -> None:
        reg = RemoteRegistry(tmp_path / "skills")
        reg.register_remote(PluginManifest(name="p", version="1.0"))
        reg.install("p")
        reg.register_remote(PluginManifest(name="p", version="2.0"))
        reg.update("p")
        assert reg.get_installed("p").version == "2.0"
        result = reg.rollback("p")
        assert result.status == InstallStatus.INSTALLED
        assert result.version == "1.0"
        assert reg.get_installed("p").version == "1.0"

    def test_rollback_no_history(self, tmp_path: Path) -> None:
        reg = RemoteRegistry(tmp_path / "skills")
        reg.register_remote(PluginManifest(name="p", version="1.0"))
        reg.install("p")
        result = reg.rollback("p")
        assert result.status == InstallStatus.FAILED
        assert "No previous version" in result.message

    def test_rollback_not_installed(self, tmp_path: Path) -> None:
        reg = RemoteRegistry(tmp_path / "skills")
        result = reg.rollback("missing")
        assert result.status == InstallStatus.FAILED


# ============================================================================
# RemoteRegistry — Uninstall
# ============================================================================


class TestRemoteRegistryUninstall:
    def test_uninstall(self, tmp_path: Path) -> None:
        reg = RemoteRegistry(tmp_path / "skills")
        reg.register_remote(PluginManifest(name="p", version="1.0"))
        reg.install("p")
        result = reg.uninstall("p")
        assert result.status == InstallStatus.NOT_INSTALLED
        assert reg.get_installed("p") is None

    def test_uninstall_not_installed(self, tmp_path: Path) -> None:
        reg = RemoteRegistry(tmp_path / "skills")
        result = reg.uninstall("missing")
        assert result.status == InstallStatus.FAILED


# ============================================================================
# RemoteRegistry — Search & Discovery
# ============================================================================


class TestRemoteRegistrySearch:
    def test_search_by_name(self, tmp_path: Path) -> None:
        reg = RemoteRegistry(tmp_path / "skills")
        reg.register_remote(PluginManifest(name="weather", version="1.0", description="Weather"))
        reg.register_remote(PluginManifest(name="calendar", version="1.0", description="Calendar"))
        results = reg.search("weather")
        assert len(results) == 1
        assert results[0].name == "weather"

    def test_search_by_category(self, tmp_path: Path) -> None:
        reg = RemoteRegistry(tmp_path / "skills")
        reg.register_remote(PluginManifest(name="a", version="1.0", category="tools"))
        reg.register_remote(PluginManifest(name="b", version="1.0", category="finance"))
        results = reg.search(category="tools")
        assert len(results) == 1

    def test_search_by_tags(self, tmp_path: Path) -> None:
        reg = RemoteRegistry(tmp_path / "skills")
        reg.register_remote(PluginManifest(name="a", version="1.0", tags=["ai", "ml"]))
        reg.register_remote(PluginManifest(name="b", version="1.0", tags=["web"]))
        results = reg.search(tags=["ai"])
        assert len(results) == 1

    def test_search_empty(self, tmp_path: Path) -> None:
        reg = RemoteRegistry(tmp_path / "skills")
        assert reg.search("nonexistent") == []

    def test_check_updates(self, tmp_path: Path) -> None:
        reg = RemoteRegistry(tmp_path / "skills")
        reg.register_remote(PluginManifest(name="p", version="1.0"))
        reg.install("p")
        reg.register_remote(PluginManifest(name="p", version="2.0"))
        updates = reg.check_updates()
        assert len(updates) == 1
        assert updates[0]["available_version"] == "2.0"


# ============================================================================
# RemoteRegistry — Persistence
# ============================================================================


class TestRemoteRegistryPersistence:
    def test_history_persists(self, tmp_path: Path) -> None:
        skills = tmp_path / "skills"
        reg1 = RemoteRegistry(skills)
        reg1.register_remote(PluginManifest(name="p", version="1.0"))
        reg1.install("p")

        reg2 = RemoteRegistry(skills)
        assert reg2.get_installed("p") is not None
        assert reg2.get_installed("p").version == "1.0"

    def test_stats(self, tmp_path: Path) -> None:
        reg = RemoteRegistry(tmp_path / "skills")
        reg.register_remote(PluginManifest(name="a", version="1.0"))
        reg.register_remote(PluginManifest(name="b", version="1.0", signature="sig"))
        reg.install("a")
        s = reg.stats()
        assert s["registry_plugins"] == 2
        assert s["installed_plugins"] == 1
        assert s["signed_plugins"] == 1
