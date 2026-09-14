"""Tests fuer F-028: Hardcoded Unix Paths in multitenant.py.

Prueft dass:
  - data_path plattformunabhaengig ist (kein /data/tenants/)
  - secrets_path plattformunabhaengig ist (kein /run/secrets/)
  - Pfade den tenant_id enthalten
  - Pfade unter ~/.cognithor/tenants/ liegen
  - Path-Objekte korrekt aufgeloest werden
  - Source-Code keine hardcoded Unix-Pfade mehr hat
"""

from __future__ import annotations

import inspect
from pathlib import Path

from cognithor.core.multitenant import Tenant, TenantManager, TenantPlan

# ============================================================================
# Plattformunabhaengige Pfade
# ============================================================================


class TestPlatformIndependentPaths:
    """Prueft dass Pfade plattformunabhaengig sind."""

    def test_data_path_no_unix_hardcode(self) -> None:
        """data_path darf nicht mit /data/tenants/ beginnen."""
        t = Tenant(tenant_id="test123", name="Test")
        assert not t.data_path.startswith("/data/tenants/")

    def test_secrets_path_no_unix_hardcode(self) -> None:
        """secrets_path darf nicht mit /run/secrets/ beginnen."""
        t = Tenant(tenant_id="test123", name="Test")
        assert not t.secrets_path.startswith("/run/secrets/")

    def test_data_path_uses_home_dir(self) -> None:
        """data_path liegt unter Home-Verzeichnis."""
        t = Tenant(tenant_id="test123", name="Test")
        home = str(Path.home())
        assert t.data_path.startswith(home)

    def test_secrets_path_uses_home_dir(self) -> None:
        """secrets_path liegt unter Home-Verzeichnis."""
        t = Tenant(tenant_id="test123", name="Test")
        home = str(Path.home())
        assert t.secrets_path.startswith(home)

    def test_paths_use_os_separator(self) -> None:
        """Pfade verwenden den OS-spezifischen Separator."""
        t = Tenant(tenant_id="test123", name="Test")
        # Path.home() / ... erzeugt automatisch OS-spezifische Separatoren
        data_p = Path(t.data_path)
        secrets_p = Path(t.secrets_path)
        assert data_p.is_absolute()
        assert secrets_p.is_absolute()


# ============================================================================
# Tenant-ID im Pfad
# ============================================================================


class TestTenantIdInPath:
    """Prueft dass Pfade die tenant_id enthalten."""

    def test_data_path_contains_tenant_id(self) -> None:
        t = Tenant(tenant_id="abc999", name="T")
        assert "abc999" in t.data_path

    def test_secrets_path_contains_tenant_id(self) -> None:
        t = Tenant(tenant_id="abc999", name="T")
        assert "abc999" in t.secrets_path

    def test_different_tenants_different_paths(self) -> None:
        t1 = Tenant(tenant_id="tenant_a", name="A")
        t2 = Tenant(tenant_id="tenant_b", name="B")
        assert t1.data_path != t2.data_path
        assert t1.secrets_path != t2.secrets_path

    def test_data_and_secrets_paths_differ(self) -> None:
        t = Tenant(tenant_id="x", name="X")
        assert t.data_path != t.secrets_path


# ============================================================================
# Pfad-Struktur
# ============================================================================


class TestPathStructure:
    """Prueft die Verzeichnisstruktur."""

    def test_data_path_under_jarvis_tenants(self) -> None:
        t = Tenant(tenant_id="t1", name="T")
        p = Path(t.data_path)
        # Erwartete Struktur: ~/.cognithor/tenants/t1/data
        parts = p.parts
        assert "tenants" in parts
        assert "t1" in parts
        assert parts[-1] == "data"

    def test_secrets_path_under_jarvis_tenants(self) -> None:
        t = Tenant(tenant_id="t1", name="T")
        p = Path(t.secrets_path)
        parts = p.parts
        assert "tenants" in parts
        assert "t1" in parts
        assert parts[-1] == "secrets"

    def test_to_dict_includes_data_path(self) -> None:
        t = Tenant(tenant_id="x", name="X")
        d = t.to_dict()
        assert "data_path" in d
        assert "x" in d["data_path"]

    def test_manager_created_tenant_has_valid_paths(self) -> None:
        """Von TenantManager erstellter Tenant hat gueltige Pfade."""
        mgr = TenantManager()
        t = mgr.create("TestOrg", "admin@test.de", plan=TenantPlan.STARTER)
        p = Path(t.data_path)
        assert p.is_absolute()
        assert t.tenant_id in str(p)


# ============================================================================
# Source-Level-Checks
# ============================================================================


class TestSourceLevelChecks:
    """Prueft den Source-Code auf den Fix."""

    def test_no_hardcoded_data_tenants_path(self) -> None:
        """Source-Code darf kein '/data/tenants/' mehr enthalten."""
        source = inspect.getsource(Tenant.data_path.fget)
        assert "/data/tenants/" not in source

    def test_no_hardcoded_run_secrets_path(self) -> None:
        """Source-Code darf kein '/run/secrets/tenants/' mehr enthalten."""
        source = inspect.getsource(Tenant.secrets_path.fget)
        assert "/run/secrets/" not in source

    def test_uses_path_home(self) -> None:
        """Source-Code verwendet Path.home()."""
        source = inspect.getsource(Tenant.data_path.fget)
        assert "Path.home()" in source

    def test_path_imported(self) -> None:
        """Path wird importiert."""
        import cognithor.core.multitenant as mod

        source = inspect.getsource(mod)
        assert "from pathlib import Path" in source
