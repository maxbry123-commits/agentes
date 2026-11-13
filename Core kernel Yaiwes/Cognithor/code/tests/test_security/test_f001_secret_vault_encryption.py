"""Tests fuer F-001: PerAgentSecretVault muss echte Verschluesselung verwenden.

Prueft dass:
  - store() + retrieve() einen vollstaendigen Roundtrip liefern (Originalwert zurueck)
  - Der gespeicherte Ciphertext NICHT der Originalwert ist
  - Der gespeicherte Ciphertext NICHT ein SHA-256-Hash ist
  - Cross-Agent-Zugriff blockiert wird
  - Verschiedene Agenten verschiedene Ciphertexte fuer denselben Wert produzieren
  - revoke() und revoke_all() korrekt aufraeumen
  - Unicode-Secrets korrekt roundtrippen
  - Leere Strings korrekt behandelt werden
  - Mehrere Secrets pro Agent unabhaengig funktionieren
  - Nach revoke_all sind Crypto-Keys entfernt
"""

from __future__ import annotations

import hashlib

from cognithor.security.sandbox_isolation import PerAgentSecretVault


class TestSecretVaultRoundtrip:
    """Kerntest: store() -> retrieve() gibt den Originalwert zurueck."""

    def test_basic_roundtrip(self) -> None:
        vault = PerAgentSecretVault()
        vault.store("agent-1", "api_key", "my-secret-value-123")
        result = vault.retrieve("agent-1", "api_key")
        assert result == "my-secret-value-123"

    def test_roundtrip_multiple_secrets(self) -> None:
        vault = PerAgentSecretVault()
        vault.store("agent-1", "key1", "value-alpha")
        vault.store("agent-1", "key2", "value-beta")
        vault.store("agent-1", "key3", "value-gamma")
        assert vault.retrieve("agent-1", "key1") == "value-alpha"
        assert vault.retrieve("agent-1", "key2") == "value-beta"
        assert vault.retrieve("agent-1", "key3") == "value-gamma"

    def test_roundtrip_unicode(self) -> None:
        vault = PerAgentSecretVault()
        secret = "Geheimer-Schluessel-mit-Umlauten-aeoue-und-Sonderzeichen-!@#$%"
        vault.store("agent-1", "unicode_key", secret)
        assert vault.retrieve("agent-1", "unicode_key") == secret

    def test_roundtrip_long_value(self) -> None:
        vault = PerAgentSecretVault()
        long_secret = "x" * 10_000
        vault.store("agent-1", "long", long_secret)
        assert vault.retrieve("agent-1", "long") == long_secret

    def test_roundtrip_empty_string(self) -> None:
        vault = PerAgentSecretVault()
        vault.store("agent-1", "empty", "")
        assert vault.retrieve("agent-1", "empty") == ""

    def test_roundtrip_special_chars(self) -> None:
        vault = PerAgentSecretVault()
        secret = "quotes\"and'backslash\\newline\ntab\tnull\x00end"
        vault.store("agent-1", "special", secret)
        assert vault.retrieve("agent-1", "special") == secret

    def test_roundtrip_json_payload(self) -> None:
        vault = PerAgentSecretVault()
        secret = '{"access_token": "eyJhbGciOiJSUzI1NiJ9", "expires_in": 3600}'
        vault.store("agent-1", "oauth", secret)
        assert vault.retrieve("agent-1", "oauth") == secret


class TestEncryptionQuality:
    """Prueft dass der gespeicherte Wert tatsaechlich verschluesselt ist."""

    def test_ciphertext_is_not_plaintext(self) -> None:
        vault = PerAgentSecretVault()
        original = "super-secret-password"
        secret_obj = vault.store("agent-1", "pw", original)
        assert secret_obj.encrypted_value != original

    def test_ciphertext_is_not_sha256_hash(self) -> None:
        """DER KERNTEST: Der alte Bug war SHA-256 statt Encryption."""
        vault = PerAgentSecretVault()
        original = "super-secret-password"
        secret_obj = vault.store("agent-1", "pw", original)
        sha256_hash = hashlib.sha256(original.encode()).hexdigest()
        assert secret_obj.encrypted_value != sha256_hash, (
            "Ciphertext darf NICHT der SHA-256-Hash des Originalwerts sein! "
            "Das wuerde bedeuten, dass der Originalwert nicht wiederherstellbar ist."
        )

    def test_ciphertext_is_not_md5_hash(self) -> None:
        vault = PerAgentSecretVault()
        original = "test-value"
        secret_obj = vault.store("agent-1", "k", original)
        md5_hash = hashlib.md5(original.encode()).hexdigest()
        assert secret_obj.encrypted_value != md5_hash

    def test_same_value_different_ciphertext(self) -> None:
        """Fernet erzeugt bei jedem Aufruf einen anderen Ciphertext (IV/Nonce)."""
        vault = PerAgentSecretVault()
        s1 = vault.store("agent-1", "k1", "same-value")
        s2 = vault.store("agent-1", "k2", "same-value")
        assert s1.encrypted_value != s2.encrypted_value

    def test_different_agents_different_ciphertext(self) -> None:
        """Verschiedene Agenten haben verschiedene Keys -> verschiedene Ciphertexte."""
        vault = PerAgentSecretVault()
        s1 = vault.store("agent-1", "k", "shared-secret")
        s2 = vault.store("agent-2", "k", "shared-secret")
        assert s1.encrypted_value != s2.encrypted_value

    def test_ciphertext_looks_like_fernet_token(self) -> None:
        """Fernet-Tokens beginnen mit 'gAAAAA' (base64-encoded version byte 0x80)."""
        vault = PerAgentSecretVault()
        secret_obj = vault.store("agent-1", "k", "test")
        assert secret_obj.encrypted_value.startswith("gAAAAA"), (
            f"Ciphertext sieht nicht wie ein Fernet-Token aus: {secret_obj.encrypted_value[:20]}..."
        )


class TestCrossAgentIsolation:
    """Prueft dass Cross-Agent-Zugriff blockiert wird."""

    def test_cross_agent_retrieve_blocked(self) -> None:
        vault = PerAgentSecretVault()
        vault.store("agent-1", "secret_key", "my-secret")
        result = vault.retrieve("agent-1", "secret_key", requesting_agent="agent-2")
        assert result is None

    def test_own_agent_retrieve_allowed(self) -> None:
        vault = PerAgentSecretVault()
        vault.store("agent-1", "secret_key", "my-secret")
        result = vault.retrieve("agent-1", "secret_key", requesting_agent="agent-1")
        assert result == "my-secret"

    def test_default_requester_is_self(self) -> None:
        vault = PerAgentSecretVault()
        vault.store("agent-1", "k", "v")
        # Ohne requesting_agent -> der Agent selbst
        result = vault.retrieve("agent-1", "k")
        assert result == "v"

    def test_blocked_attempts_logged(self) -> None:
        vault = PerAgentSecretVault()
        vault.store("agent-1", "k", "v")
        vault.retrieve("agent-1", "k", requesting_agent="evil-agent")
        vault.retrieve("agent-1", "k", requesting_agent="another-evil")
        blocked = vault.blocked_attempts()
        assert len(blocked) == 2
        assert blocked[0]["requester"] == "evil-agent"
        assert blocked[1]["requester"] == "another-evil"

    def test_agent_cannot_read_other_agents_keys(self) -> None:
        vault = PerAgentSecretVault()
        vault.store("agent-1", "k1", "secret-1")
        vault.store("agent-2", "k2", "secret-2")
        # agent-1 kann nur seine eigenen Keys sehen
        assert vault.list_keys("agent-1") == ["k1"]
        assert vault.list_keys("agent-2") == ["k2"]


class TestRevocation:
    """Prueft revoke() und revoke_all()."""

    def test_revoke_single(self) -> None:
        vault = PerAgentSecretVault()
        vault.store("agent-1", "k1", "v1")
        vault.store("agent-1", "k2", "v2")
        assert vault.revoke("agent-1", "k1") is True
        assert vault.retrieve("agent-1", "k1") is None
        assert vault.retrieve("agent-1", "k2") == "v2"

    def test_revoke_nonexistent(self) -> None:
        vault = PerAgentSecretVault()
        assert vault.revoke("agent-1", "nonexistent") is False

    def test_revoke_all_clears_secrets(self) -> None:
        vault = PerAgentSecretVault()
        vault.store("agent-1", "k1", "v1")
        vault.store("agent-1", "k2", "v2")
        count = vault.revoke_all("agent-1")
        assert count == 2
        assert vault.total_secrets == 0

    def test_revoke_all_clears_crypto_keys(self) -> None:
        """Nach revoke_all muessen auch die Crypto-Keys entfernt sein."""
        vault = PerAgentSecretVault()
        vault.store("agent-1", "k", "v")
        assert "agent-1" in vault._fernets
        assert "agent-1" in vault._salts
        vault.revoke_all("agent-1")
        assert "agent-1" not in vault._fernets
        assert "agent-1" not in vault._salts

    def test_revoke_all_nonexistent_agent(self) -> None:
        vault = PerAgentSecretVault()
        count = vault.revoke_all("ghost-agent")
        assert count == 0

    def test_store_after_revoke_all_works(self) -> None:
        """Nach revoke_all muss ein neuer Store mit neuem Key funktionieren."""
        vault = PerAgentSecretVault()
        vault.store("agent-1", "k", "old-value")
        vault.revoke_all("agent-1")
        vault.store("agent-1", "k", "new-value")
        assert vault.retrieve("agent-1", "k") == "new-value"


class TestRetrieveEdgeCases:
    """Prueft Edge Cases bei retrieve()."""

    def test_retrieve_nonexistent_key(self) -> None:
        vault = PerAgentSecretVault()
        vault.store("agent-1", "k", "v")
        assert vault.retrieve("agent-1", "nonexistent") is None

    def test_retrieve_nonexistent_agent(self) -> None:
        vault = PerAgentSecretVault()
        assert vault.retrieve("ghost-agent", "k") is None

    def test_overwrite_secret(self) -> None:
        vault = PerAgentSecretVault()
        vault.store("agent-1", "k", "original")
        vault.store("agent-1", "k", "updated")
        assert vault.retrieve("agent-1", "k") == "updated"


class TestStats:
    """Prueft Statistik-Funktionen."""

    def test_total_secrets(self) -> None:
        vault = PerAgentSecretVault()
        assert vault.total_secrets == 0
        vault.store("a1", "k1", "v1")
        vault.store("a2", "k2", "v2")
        assert vault.total_secrets == 2

    def test_stats_dict(self) -> None:
        vault = PerAgentSecretVault()
        vault.store("a1", "k", "v")
        stats = vault.stats()
        assert stats["agents_with_secrets"] == 1
        assert stats["total_secrets"] == 1
        assert stats["total_access_attempts"] == 0

    def test_list_keys(self) -> None:
        vault = PerAgentSecretVault()
        vault.store("a1", "alpha", "v1")
        vault.store("a1", "beta", "v2")
        keys = vault.list_keys("a1")
        assert sorted(keys) == ["alpha", "beta"]

    def test_list_keys_empty(self) -> None:
        vault = PerAgentSecretVault()
        assert vault.list_keys("nonexistent") == []

    def test_to_dict_does_not_leak_value(self) -> None:
        """AgentSecret.to_dict() darf den verschluesselten Wert nicht enthalten."""
        vault = PerAgentSecretVault()
        secret_obj = vault.store("a1", "k", "super-secret")
        d = secret_obj.to_dict()
        assert "encrypted_value" not in d
        assert "super-secret" not in str(d)


class TestMultiTenant:
    """Prueft tenant_id Isolation."""

    def test_same_key_different_tenants(self) -> None:
        vault = PerAgentSecretVault()
        vault.store("agent-1", "k", "tenant-a-secret", tenant_id="tenant-a")
        vault.store("agent-1", "k", "tenant-b-secret", tenant_id="tenant-b")
        # Letzter store ueberschreibt (gleicher agent_id + key)
        result = vault.retrieve("agent-1", "k")
        assert result == "tenant-b-secret"

    def test_tenant_id_stored(self) -> None:
        vault = PerAgentSecretVault()
        secret_obj = vault.store("agent-1", "k", "v", tenant_id="acme-corp")
        assert secret_obj.tenant_id == "acme-corp"
