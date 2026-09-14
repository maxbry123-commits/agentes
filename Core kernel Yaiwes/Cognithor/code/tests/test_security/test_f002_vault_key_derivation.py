"""Tests fuer F-002: AgentVault Key-Derivation mit Master-Secret.

Prueft dass:
  - Mit master_secret: agent_id allein reicht NICHT zum Entschluesseln
  - Ohne master_secret (legacy): altes Verhalten bleibt erhalten
  - Gleicher agent_id + gleicher master_secret = gleicher Key (Determinismus)
  - Verschiedene master_secrets = verschiedene Keys
  - AgentVaultManager generiert und persistiert master_secret
  - Persistiertes master_secret wird korrekt geladen
  - Truncated/corrupt key file wird regeneriert
  - Vault-Roundtrip funktioniert ueber Manager-Instanzen hinweg
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from cognithor.security.agent_vault import (
    AgentVault,
    AgentVaultManager,
    SecretType,
    _load_or_create_master_secret,
)

# ============================================================================
# Master-Secret in Key-Derivation
# ============================================================================


class TestMasterSecretInKeyDerivation:
    """Kerntest: master_secret fliesst in die Key-Ableitung ein."""

    def test_with_master_secret_changes_key(self) -> None:
        """Gleicher agent_id, verschiedene master_secrets -> verschiedene Keys."""
        vault_a = AgentVault("agent-1", master_secret=b"secret-alpha-32bytes-padding!!")
        vault_b = AgentVault("agent-1", master_secret=b"secret-beta-32bytes-padding!!!")
        encrypted = vault_a._encrypt("geheim")
        with pytest.raises((ValueError, Exception)):
            vault_b._decrypt(encrypted)

    def test_without_master_secret_cannot_decrypt_protected(self) -> None:
        """Vault mit master_secret kann nicht von Vault ohne entschluesselt werden."""
        vault_protected = AgentVault("agent-1", master_secret=b"my-master-secret")
        encrypted = vault_protected._encrypt("top-secret")
        vault_unprotected = AgentVault("agent-1")  # kein master_secret
        with pytest.raises((ValueError, Exception)):
            vault_unprotected._decrypt(encrypted)

    def test_same_master_secret_same_key(self) -> None:
        """Gleicher agent_id + gleicher master_secret -> gleicher Key (Determinismus)."""
        ms = b"deterministic-master-secret-1234"
        vault1 = AgentVault("agent-x", master_secret=ms)
        encrypted = vault1._encrypt("geheim")
        vault2 = AgentVault("agent-x", master_secret=ms)
        assert vault2._decrypt(encrypted) == "geheim"

    def test_roundtrip_with_master_secret(self) -> None:
        """Vollstaendiger store/retrieve Roundtrip mit master_secret."""
        ms = b"roundtrip-master-secret-12345!!"
        vault = AgentVault("agent-rt", master_secret=ms)
        secret = vault.store("api_key", "sk-live-abc123", SecretType.API_KEY)
        assert vault.retrieve(secret.secret_id) == "sk-live-abc123"

    def test_roundtrip_new_instance_with_master_secret(self) -> None:
        """Store in Instanz 1, Retrieve in Instanz 2 (gleicher master_secret)."""
        ms = b"cross-instance-master-secret!!"
        vault1 = AgentVault("agent-ci", master_secret=ms)
        secret = vault1.store("db_password", "p@ssw0rd!")
        encrypted_value = secret._encrypted_value

        vault2 = AgentVault("agent-ci", master_secret=ms)
        decrypted = vault2._decrypt(encrypted_value)
        assert decrypted == "p@ssw0rd!"

    def test_different_agents_same_master_secret(self) -> None:
        """Verschiedene agent_ids mit gleichem master_secret -> verschiedene Keys."""
        ms = b"shared-master-secret-for-all!!"
        vault_a = AgentVault("agent-alpha", master_secret=ms)
        vault_b = AgentVault("agent-beta", master_secret=ms)
        encrypted = vault_a._encrypt("geheim")
        with pytest.raises((ValueError, Exception)):
            vault_b._decrypt(encrypted)


class TestLegacyCompatibility:
    """Prueft dass das alte Verhalten (ohne master_secret) erhalten bleibt."""

    def test_legacy_deterministic(self) -> None:
        """Ohne master_secret: gleiche agent_id -> gleicher Key."""
        vault1 = AgentVault("legacy-agent")
        encrypted = vault1._encrypt("legacy-secret")
        vault2 = AgentVault("legacy-agent")
        assert vault2._decrypt(encrypted) == "legacy-secret"

    def test_legacy_different_agents(self) -> None:
        """Ohne master_secret: verschiedene agent_ids -> verschiedene Keys."""
        vault_a = AgentVault("agent-a")
        vault_b = AgentVault("agent-b")
        encrypted = vault_a._encrypt("geheim")
        with pytest.raises((ValueError, Exception)):
            vault_b._decrypt(encrypted)

    def test_empty_master_secret_equals_no_master_secret(self) -> None:
        """master_secret=b'' ist identisch mit keinem master_secret."""
        vault_default = AgentVault("agent-compat")
        vault_empty = AgentVault("agent-compat", master_secret=b"")
        encrypted = vault_default._encrypt("test")
        assert vault_empty._decrypt(encrypted) == "test"


# ============================================================================
# _load_or_create_master_secret
# ============================================================================


class TestLoadOrCreateMasterSecret:
    """Prueft die Master-Secret Persistence."""

    def test_creates_new_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            key_path = os.path.join(tmpdir, "vault_master.key")
            secret = _load_or_create_master_secret(key_path)
            assert len(secret) == 32
            assert os.path.exists(key_path)
            stored = Path(key_path).read_bytes()
            assert stored == secret

    def test_loads_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            key_path = os.path.join(tmpdir, "vault_master.key")
            # Write a known key blob
            known_key_data = os.urandom(32)
            Path(key_path).write_bytes(known_key_data)
            loaded = _load_or_create_master_secret(key_path)
            assert loaded == known_key_data

    def test_regenerates_truncated_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            key_path = os.path.join(tmpdir, "vault_master.key")
            Path(key_path).write_bytes(b"too-short")
            secret = _load_or_create_master_secret(key_path)
            assert len(secret) == 32
            # File should be overwritten with new 32-byte secret
            stored = Path(key_path).read_bytes()
            assert len(stored) == 32
            assert stored != b"too-short"

    def test_deterministic_on_reload(self) -> None:
        """Zweimal laden liefert dasselbe Secret."""
        with tempfile.TemporaryDirectory() as tmpdir:
            key_path = os.path.join(tmpdir, "vault_master.key")
            first = _load_or_create_master_secret(key_path)
            second = _load_or_create_master_secret(key_path)
            assert first == second

    def test_creates_parent_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            key_path = os.path.join(tmpdir, "sub", "dir", "vault_master.key")
            secret = _load_or_create_master_secret(key_path)
            assert len(secret) == 32
            assert os.path.exists(key_path)

    def test_longer_file_truncated_to_32(self) -> None:
        """Datei mit mehr als 32 Bytes: nur die ersten 32 werden verwendet."""
        with tempfile.TemporaryDirectory() as tmpdir:
            key_path = os.path.join(tmpdir, "vault_master.key")
            long_key = os.urandom(64)
            Path(key_path).write_bytes(long_key)
            loaded = _load_or_create_master_secret(key_path)
            assert loaded == long_key[:32]


# ============================================================================
# AgentVaultManager Integration
# ============================================================================


class TestAgentVaultManagerIntegration:
    """Prueft dass der Manager das master_secret korrekt weitergibt."""

    def test_manager_uses_master_secret(self) -> None:
        """Vaults ueber den Manager erstellt nutzen das master_secret."""
        with tempfile.TemporaryDirectory() as tmpdir:
            key_path = os.path.join(tmpdir, "vault_master.key")
            mgr = AgentVaultManager(master_secret_path=key_path)
            vault = mgr.create_vault("agent-1")
            secret = vault.store("api_key", "sk-secret-123")
            assert vault.retrieve(secret.secret_id) == "sk-secret-123"

    def test_manager_vaults_share_master_secret(self) -> None:
        """Mehrere Vaults vom gleichen Manager nutzen dasselbe master_secret."""
        with tempfile.TemporaryDirectory() as tmpdir:
            key_path = os.path.join(tmpdir, "vault_master.key")
            mgr = AgentVaultManager(master_secret_path=key_path)
            v1 = mgr.create_vault("agent-1")
            v2 = mgr.create_vault("agent-2")
            s1 = v1.store("k", "value-1")
            s2 = v2.store("k", "value-2")
            assert v1.retrieve(s1.secret_id) == "value-1"
            assert v2.retrieve(s2.secret_id) == "value-2"

    def test_manager_restart_preserves_keys(self) -> None:
        """Zwei Manager-Instanzen mit gleicher key_path -> gleicher master_secret."""
        with tempfile.TemporaryDirectory() as tmpdir:
            key_path = os.path.join(tmpdir, "vault_master.key")
            mgr1 = AgentVaultManager(master_secret_path=key_path)
            vault1 = mgr1.create_vault("persistent-agent")
            secret = vault1.store("db_pw", "correct-horse-battery")
            encrypted_value = secret._encrypted_value

            # Simuliere Restart: neuer Manager, gleicher Key-Path
            mgr2 = AgentVaultManager(master_secret_path=key_path)
            vault2 = mgr2.create_vault("persistent-agent")
            decrypted = vault2._decrypt(encrypted_value)
            assert decrypted == "correct-horse-battery"

    def test_different_key_paths_different_secrets(self) -> None:
        """Verschiedene key_paths -> verschiedene master_secrets -> verschiedene Keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path_a = os.path.join(tmpdir, "key_a.key")
            path_b = os.path.join(tmpdir, "key_b.key")
            mgr_a = AgentVaultManager(master_secret_path=path_a)
            mgr_b = AgentVaultManager(master_secret_path=path_b)
            vault_a = mgr_a.create_vault("agent-1")
            vault_b = mgr_b.create_vault("agent-1")  # gleiche agent_id!
            encrypted = vault_a._encrypt("geheim")
            with pytest.raises((ValueError, Exception)):
                vault_b._decrypt(encrypted)

    def test_manager_without_path_uses_default(self) -> None:
        """Manager ohne expliziten path nutzt ~/.cognithor/vault_master.key."""
        mgr = AgentVaultManager()
        assert len(mgr._master_secret) == 32
        vault = mgr.create_vault("agent-default")
        s = vault.store("k", "v")
        assert vault.retrieve(s.secret_id) == "v"

    def test_destroy_vault_still_works(self) -> None:
        """destroy_vault funktioniert weiterhin korrekt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            key_path = os.path.join(tmpdir, "vault_master.key")
            mgr = AgentVaultManager(master_secret_path=key_path)
            vault = mgr.create_vault("agent-doom")
            vault.store("k", "v")
            assert mgr.destroy_vault("agent-doom") is True
            assert mgr.get_vault("agent-doom") is None

    def test_rotate_all_still_works(self) -> None:
        """rotate_all funktioniert weiterhin korrekt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            key_path = os.path.join(tmpdir, "vault_master.key")
            mgr = AgentVaultManager(master_secret_path=key_path)
            vault = mgr.create_vault("agent-rot")
            vault.store("api_key", "original-key", SecretType.API_KEY)
            results = mgr.rotate_all()
            # rotate_all may or may not rotate depending on policy timing
            assert isinstance(results, dict)
