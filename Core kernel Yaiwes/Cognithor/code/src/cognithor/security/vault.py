"""Cognithor · Encrypted Agent Vaults & Isolated Session Stores.

Complete encapsulation per agent:

  - EncryptedVault:       Encrypted token vault per agent (Fernet)
  - IsolatedSessionStore: Separate session stores per agent
  - VaultManager:         Orchestrates all agent vaults
  - SessionIsolationGuard: Enforces session separation

Architecture Bible: §11.4 (Credential-Isolation), §14.3 (Multi-Tenant)

Problem statement:
  The existing Agent OS separates workspaces and sets quotas,
  but stores sessions and credentials centrally. Separate
  encrypted stores per agent improve multi-user suitability.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

_vault_log = logging.getLogger(__name__)


# ============================================================================
# Encryption Layer (Fernet-compatible, Zero-Dependency)
# ============================================================================


class _SimpleEncryptor:
    """Fernet-based authenticated encryption with PBKDF2 key derivation.

    Uses ``cryptography.fernet.Fernet`` for AES-128-CBC encryption with
    HMAC-SHA256 authentication.  The caller-supplied key is stretched via
    PBKDF2-HMAC-SHA256 (480 000 iterations) to derive the 32-byte Fernet
    key.  A stable per-instance salt is generated on construction so that
    the same encryptor can round-trip data it produced.
    """

    def __init__(self, key: bytes) -> None:
        self._raw_key = key
        self._salt = os.urandom(16)
        self._fernet = self._build_fernet(key, self._salt)

    # -- public API (same signatures as before) --------------------------------

    def encrypt(self, data: str) -> str:
        """Encrypt a string and return a Fernet token prefixed with the salt.

        Format: ``base64(salt)`` + ``.`` + ``<fernet-token>``
        The salt prefix lets ``decrypt`` re-derive the same Fernet key.
        """
        token = self._fernet.encrypt(data.encode("utf-8")).decode("ascii")
        salt_b64 = base64.urlsafe_b64encode(self._salt).decode("ascii")
        return f"{salt_b64}.{token}"

    def decrypt(self, token: str) -> str:
        """Decrypt a Fernet token (with embedded salt) back to a string.

        Falls back to the legacy XOR-HMAC format when the token does not
        contain the salt prefix so that data encrypted before the migration
        can still be read.
        """
        if "." in token:
            salt_b64, fernet_token = token.split(".", 1)
            salt = base64.urlsafe_b64decode(salt_b64)
            fernet = self._build_fernet(self._raw_key, salt)
            return fernet.decrypt(fernet_token.encode("ascii")).decode("utf-8")

        # Legacy fallback: old XOR-HMAC encrypted data (deprecated, insecure)
        import warnings

        _legacy_log = logging.getLogger(__name__)
        _legacy_log.warning(
            "SECURITY: Legacy XOR-HMAC encryption detected. "
            "This cipher is cryptographically weak and will be removed in a "
            "future version. The entry will be auto-migrated to Fernet on "
            "next vault read."
        )
        warnings.warn(
            "Legacy XOR-HMAC encryption is deprecated and insecure. "
            "Entry will be auto-migrated to Fernet.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._legacy_decrypt(token)

    # -- internals -------------------------------------------------------------

    @staticmethod
    def _build_fernet(key: bytes, salt: bytes) -> Fernet:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600_000,
        )
        derived = kdf.derive(hashlib.sha256(key).digest())
        return Fernet(base64.urlsafe_b64encode(derived))

    def _legacy_decrypt(self, token: str) -> str:
        """Decrypt data produced by the old XOR-HMAC encryptor.

        Kept only for backward compatibility during migration.
        """
        raw_key = hashlib.sha256(self._raw_key).digest()
        try:
            raw = base64.b64decode(token)
        except Exception as exc:
            raise ValueError(f"Invalid token format (Base64 error): {exc}") from exc
        if len(raw) < 33:  # at least 16 (IV) + 16 (MAC) + 1 (cipher)
            raise ValueError("Token too short for legacy decryption")
        iv = raw[:16]
        mac_stored = raw[16:32]
        cipher = raw[32:]
        mac_computed = hmac.new(raw_key, iv + cipher, hashlib.sha256).digest()[:16]
        if not hmac.compare_digest(mac_stored, mac_computed):
            raise ValueError("Integrity check failed: token was tampered with.")
        # Derive legacy XOR key stream
        stream = b""
        counter = 0
        while len(stream) < len(cipher):
            block = hashlib.sha256(raw_key + iv + counter.to_bytes(4, "big")).digest()
            stream += block
            counter += 1
        stream = stream[: len(cipher)]
        plaintext = bytes(a ^ b for a, b in zip(cipher, stream, strict=False))
        return plaintext.decode("utf-8")


# ============================================================================
# Encrypted Vault
# ============================================================================


@dataclass
class VaultEntry:
    """An encrypted entry in the vault."""

    service: str
    key: str
    encrypted_value: str
    created_at: str
    last_accessed: str = ""
    access_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "service": self.service,
            "key": self.key,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
        }


class EncryptedVault:
    """Encrypted credential vault for a single agent.

    Each agent gets its own vault with its own
    encryption key. Credentials are encrypted at rest.
    """

    def __init__(self, agent_id: str, master_key: bytes | None = None) -> None:
        self._agent_id = agent_id
        if master_key is None:
            _vault_log.warning(
                "EncryptedVault(%s): No master_key provided -- generating ephemeral key. "
                "Data will NOT survive restarts. Pass an explicit key for persistence.",
                agent_id,
            )
            master_key = os.urandom(32)
        # Derive agent-specific key via HMAC (prevents ambiguity from concatenation)
        agent_key = hmac.new(master_key, agent_id.encode(), hashlib.sha256).digest()
        self._encryptor = _SimpleEncryptor(agent_key)
        self._entries: dict[str, VaultEntry] = {}  # "service:key" → VaultEntry

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    def store(self, service: str, key: str, value: str) -> VaultEntry:
        """Stores a credential encrypted."""
        encrypted = self._encryptor.encrypt(value)
        entry = VaultEntry(
            service=service,
            key=key,
            encrypted_value=encrypted,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        self._entries[f"{service}:{key}"] = entry
        return entry

    def retrieve(self, service: str, key: str) -> str | None:
        """Retrieves and decrypts a credential.

        Auto-migrates legacy XOR-HMAC entries to Fernet on read.
        """
        entry = self._entries.get(f"{service}:{key}")
        if not entry:
            return None
        entry.last_accessed = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        entry.access_count += 1
        plaintext = self._encryptor.decrypt(entry.encrypted_value)
        # Auto-migrate legacy entries to Fernet
        if "." not in entry.encrypted_value:
            _vault_log.info(
                "vault_legacy_migration: re-encrypting %s:%s with Fernet",
                service,
                key,
            )
            entry.encrypted_value = self._encryptor.encrypt(plaintext)
        return plaintext

    def delete(self, service: str, key: str) -> bool:
        """Deletes a credential."""
        composite = f"{service}:{key}"
        if composite in self._entries:
            del self._entries[composite]
            return True
        return False

    def list_entries(self) -> list[dict[str, Any]]:
        """Lists all entries (without values)."""
        return [e.to_dict() for e in self._entries.values()]

    def has(self, service: str, key: str) -> bool:
        return f"{service}:{key}" in self._entries

    def clear(self) -> int:
        """Deletes all entries. Returns number deleted."""
        count = len(self._entries)
        self._entries.clear()
        return count

    def stats(self) -> dict[str, Any]:
        return {
            "agent_id": self._agent_id,
            "entry_count": len(self._entries),
            "services": list(set(e.service for e in self._entries.values())),
        }


# ============================================================================
# Vault Manager: Orchestrates all agent vaults
# ============================================================================


class VaultManager:
    """Manages encrypted vaults for all agents.

    Each agent gets its own EncryptedVault with its own key.
    Cross-agent access is strictly prevented.
    """

    def __init__(self, master_key: bytes | None = None) -> None:
        self._master_key = master_key or os.urandom(32)
        self._vaults: dict[str, EncryptedVault] = {}

    def get_vault(self, agent_id: str) -> EncryptedVault:
        """Gets (or creates) the vault for an agent."""
        if agent_id not in self._vaults:
            self._vaults[agent_id] = EncryptedVault(agent_id, self._master_key)
        return self._vaults[agent_id]

    def store(self, agent_id: str, service: str, key: str, value: str) -> VaultEntry:
        """Stores a credential for an agent."""
        return self.get_vault(agent_id).store(service, key, value)

    def retrieve(self, agent_id: str, service: str, key: str) -> str | None:
        """Gets a credential -- only from the owning vault."""
        vault = self._vaults.get(agent_id)
        if not vault:
            return None
        return vault.retrieve(service, key)

    def cross_agent_attempt(
        self, requesting_agent: str, target_agent: str, service: str, key: str
    ) -> str | None:
        """Cross-agent access. Blocks and logs foreign access attempts."""
        if requesting_agent != target_agent:
            _vault_log.warning(
                "cross_agent_access_blocked: agent=%s versuchte "
                "Zugriff auf agent=%s (service=%s, key=%s)",
                requesting_agent,
                target_agent,
                service,
                key,
            )
            return None
        return self.retrieve(requesting_agent, service, key)

    @property
    def vault_count(self) -> int:
        return len(self._vaults)

    def stats(self) -> dict[str, Any]:
        return {
            "total_vaults": len(self._vaults),
            "agents": list(self._vaults.keys()),
            "total_entries": sum(v.entry_count for v in self._vaults.values()),
        }


# ============================================================================
# Isolated Session Store
# ============================================================================


@dataclass
class AgentSession:
    """An isolated session for an agent."""

    session_id: str
    agent_id: str
    user_id: str
    token: str
    created_at: str
    expires_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    active: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "active": self.active,
        }


class IsolatedSessionStore:
    """Separate session stores per agent.

    Each agent has its own session namespace.
    Sessions cannot be read across agent boundaries.
    """

    def __init__(self) -> None:
        self._stores: dict[str, dict[str, AgentSession]] = {}  # agent_id → {session_id → session}
        self._token_index: dict[str, tuple[str, str]] = {}  # token → (agent_id, session_id)

    def create_session(
        self,
        agent_id: str,
        user_id: str,
        token: str = "",
        **metadata: Any,
    ) -> AgentSession:
        """Creates a new isolated session."""
        if not token:
            token = hashlib.sha256(os.urandom(32)).hexdigest()

        session_id = hashlib.sha256(f"{agent_id}:{user_id}:{time.time()}".encode()).hexdigest()[:16]

        session = AgentSession(
            session_id=session_id,
            agent_id=agent_id,
            user_id=user_id,
            token=token,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            metadata=dict(metadata),
        )

        if agent_id not in self._stores:
            self._stores[agent_id] = {}
        self._stores[agent_id][session_id] = session
        self._token_index[token] = (agent_id, session_id)
        return session

    def get_session(self, agent_id: str, session_id: str) -> AgentSession | None:
        """Gets a session -- only from the owning store."""
        store = self._stores.get(agent_id, {})
        return store.get(session_id)

    def get_by_token(self, token: str) -> AgentSession | None:
        """Gets a session by its token."""
        ref = self._token_index.get(token)
        if not ref:
            return None
        return self.get_session(ref[0], ref[1])

    def revoke_session(self, agent_id: str, session_id: str) -> bool:
        """Revokes a session."""
        session = self.get_session(agent_id, session_id)
        if session:
            session.active = False
            if session.token in self._token_index:
                del self._token_index[session.token]
            return True
        return False

    def agent_sessions(self, agent_id: str) -> list[AgentSession]:
        """All active sessions for an agent."""
        store = self._stores.get(agent_id, {})
        return [s for s in store.values() if s.active]

    def cross_agent_attempt(
        self, requesting_agent: str, target_agent: str, session_id: str
    ) -> AgentSession | None:
        """Cross-agent session access. Always blocked."""
        if requesting_agent != target_agent:
            return None
        return self.get_session(requesting_agent, session_id)

    @property
    def total_sessions(self) -> int:
        return sum(len(s) for s in self._stores.values())

    @property
    def active_sessions(self) -> int:
        return sum(sum(1 for s in store.values() if s.active) for store in self._stores.values())

    def stats(self) -> dict[str, Any]:
        return {
            "total_agents": len(self._stores),
            "total_sessions": self.total_sessions,
            "active_sessions": self.active_sessions,
            "per_agent": {
                agent_id: len([s for s in store.values() if s.active])
                for agent_id, store in self._stores.items()
            },
        }


# ============================================================================
# Session-Isolation-Guard
# ============================================================================


class SessionIsolationGuard:
    """Enforces strict session separation.

    Checks every access to credentials and sessions
    and logs violations.
    """

    def __init__(
        self,
        vault_manager: VaultManager,
        session_store: IsolatedSessionStore,
    ) -> None:
        self._vault = vault_manager
        self._sessions = session_store
        self._violations: list[dict[str, Any]] = []

    def check_credential_access(
        self,
        requesting_agent: str,
        target_agent: str,
        service: str,
        key: str,
    ) -> str | None:
        """Checks credential access. Blocks cross-agent."""
        if requesting_agent != target_agent:
            self._violations.append(
                {
                    "type": "credential_cross_access",
                    "requesting_agent": requesting_agent,
                    "target_agent": target_agent,
                    "service": service,
                    "key": key,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
            )
            return None
        return self._vault.retrieve(requesting_agent, service, key)

    def check_session_access(
        self,
        requesting_agent: str,
        target_agent: str,
        session_id: str,
    ) -> AgentSession | None:
        """Checks session access. Blocks cross-agent."""
        if requesting_agent != target_agent:
            self._violations.append(
                {
                    "type": "session_cross_access",
                    "requesting_agent": requesting_agent,
                    "target_agent": target_agent,
                    "session_id": session_id,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
            )
            return None
        return self._sessions.get_session(requesting_agent, session_id)

    @property
    def violation_count(self) -> int:
        return len(self._violations)

    def violations(self) -> list[dict[str, Any]]:
        return list(self._violations)

    def stats(self) -> dict[str, Any]:
        return {
            "violations": len(self._violations),
            "vault_stats": self._vault.stats(),
            "session_stats": self._sessions.stats(),
        }
