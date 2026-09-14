"""Credential manager: Secure management of secrets.

Stores credentials encrypted (Fernet/AES-256) on disk.
The planner (LLM) NEVER sees plaintext credentials.
The gatekeeper injects credentials into the executor context.

Security guarantees:
  - Credentials are encrypted with AES-256 (via Fernet)
  - Master key is derived from passphrase + salt (PBKDF2)
  - Planner has no access to the store
  - Audit log masks all credential values
  - File permissions are set to 0600

Bible reference: §11.2 (Credential-Management)
"""

from __future__ import annotations

import base64
import json
import os
import stat
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cognithor.models import CredentialEntry
from cognithor.utils.logging import get_logger

log = get_logger(__name__)

# Optional import: cryptography for Fernet
_HAS_CRYPTO = False
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    _HAS_CRYPTO = True
except ImportError:
    pass


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derives a Fernet key from passphrase + salt (PBKDF2)."""
    if not _HAS_CRYPTO:
        raise RuntimeError("cryptography package not installed. pip install cryptography")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
    return key


def _obfuscate_key(passphrase: str, salt: bytes) -> bytes:
    """Deprecated -- no longer used.

    Exists only for backward compatibility when reading old stores.
    """
    if not _HAS_CRYPTO:
        raise RuntimeError("cryptography-Paket nicht installiert. pip install cryptography")
    # Historical obfuscation function: now uses the same
    # PBKDF2 configuration as _derive_key to make brute-force attacks
    # harder, but retains the Base64 format.
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000,
    )
    key = kdf.derive(passphrase.encode())
    return base64.urlsafe_b64encode(key)


class CredentialStore:
    """Encrypted credential store. [B§11.2]

    Stores key-value pairs encrypted as JSON on disk.
    Supports two modes:
      1. Fernet (AES-256) -- when `cryptography` is installed
      2. Base64 obfuscation -- fallback for development (INSECURE)

    The planner has no direct access. Credentials are
    provided by the gatekeeper via inject_credentials().
    """

    def __init__(
        self,
        store_path: Path | None = None,
        passphrase: str | None = None,
    ) -> None:
        """Initializes the credential store.

        Args:
            store_path: Path to the encrypted store file.
            passphrase: Master passphrase for encryption.
                       If None: COGNITHOR_CREDENTIAL_KEY env variable.
        """
        self._store_path = store_path or (Path.home() / ".cognithor" / "credentials.enc")
        self._store_path.parent.mkdir(parents=True, exist_ok=True)

        self._passphrase = passphrase or os.environ.get("COGNITHOR_CREDENTIAL_KEY", "")
        if not self._passphrase:
            self._passphrase = self._try_keyring()
        self._salt = self._load_or_create_salt()
        self._fernet = self._init_fernet()
        self._entries: dict[str, _StoredCredential] = {}
        self._loaded = False

    _passphrase_warned: bool = False

    @staticmethod
    def _try_keyring() -> str:
        """Try to get or create a credential passphrase from OS keyring."""
        try:
            import keyring

            key = keyring.get_password("cognithor", "credential_key")
            if key:
                return key
            # Auto-generate and store
            import secrets

            key = secrets.token_urlsafe(32)
            keyring.set_password("cognithor", "credential_key", key)
            return key
        except Exception:
            return ""

    def _init_fernet(self) -> Any:
        """Initializes Fernet encryption."""
        if not self._passphrase:
            if not CredentialStore._passphrase_warned:
                CredentialStore._passphrase_warned = True
                log.warning(
                    "credential_store_no_passphrase: Credentials are NOT encrypted! "
                    "Set COGNITHOR_CREDENTIAL_KEY env var for encryption."
                )
            return None
        if not _HAS_CRYPTO:
            raise RuntimeError(
                "cryptography package required for credential encryption. pip install cryptography"
            )
        key = _derive_key(self._passphrase, self._salt)
        return Fernet(key)

    def _load_or_create_salt(self) -> bytes:
        """Loads or creates the salt for key derivation."""
        salt_path = self._store_path.parent / ".credential_salt"
        if salt_path.exists():
            return salt_path.read_bytes()
        salt = os.urandom(16)
        salt_path.write_bytes(salt)
        self._set_file_permissions(salt_path)
        return salt

    def store(self, service: str, key: str, value: str, agent_id: str = "") -> CredentialEntry:
        """Stores a credential.

        Args:
            service: Service name (e.g. 'telegram', 'searxng').
            key: Key (e.g. 'api_key', 'bot_token').
            value: Plaintext value.
            agent_id: Optional agent assignment. Empty = globally available.

        Returns:
            CredentialEntry (without plaintext value).
        """
        self._ensure_loaded()
        lookup = f"{service}:{key}" if not agent_id else f"{agent_id}/{service}:{key}"
        encrypted = self._encrypt(value)

        self._entries[lookup] = _StoredCredential(
            service=service,
            key=key,
            encrypted_value=encrypted,
            created_at=datetime.now(UTC),
            agent_id=agent_id,
        )
        self._save()

        log.info(
            "credential_stored",
            service=service,
            key=key,
            agent_id=agent_id or "global",
        )
        return CredentialEntry(
            service=service,
            key=key,
            encrypted=self._fernet is not None,
        )

    def retrieve(self, service: str, key: str, agent_id: str = "") -> str | None:
        """Retrieves a credential (ONLY for executor/gatekeeper).

        Checks agent-specific credentials first, then global.

        Args:
            service: Service name.
            key: Key.
            agent_id: Agent ID for scoped access.

        Returns:
            Plaintext value or None if not found.
        """
        self._ensure_loaded()

        # 1. Agent-specific credential
        if agent_id:
            agent_lookup = f"{agent_id}/{service}:{key}"
            stored = self._entries.get(agent_lookup)
            if stored:
                stored.last_accessed = datetime.now(UTC)
                return self._decrypt(stored.encrypted_value)

        # 2. Global credential (fallback)
        global_lookup = f"{service}:{key}"
        stored = self._entries.get(global_lookup)
        if not stored:
            return None

        stored.last_accessed = datetime.now(UTC)
        return self._decrypt(stored.encrypted_value)

    def delete(self, service: str, key: str, agent_id: str = "") -> bool:
        """Deletes a credential.

        Args:
            service: Service name.
            key: Key.
            agent_id: If set, delete agent-specific credential.

        Returns:
            True if deleted, False if not found.
        """
        self._ensure_loaded()
        if agent_id:
            lookup = f"{agent_id}/{service}:{key}"
            if lookup in self._entries:
                del self._entries[lookup]
                self._save()
                log.info("credential_deleted", service=service, key=key, agent_id=agent_id)
                return True
            return False
        lookup = f"{service}:{key}"
        if lookup not in self._entries:
            return False

        del self._entries[lookup]
        self._save()
        log.info("credential_deleted", service=service, key=key)
        return True

    def list_entries(self, agent_id: str = "") -> list[CredentialEntry]:
        """Lists credentials (without values).

        Args:
            agent_id: If set, only credentials of this agent + global.
                     Empty = all credentials.

        Returns:
            List of CredentialEntry objects.
        """
        self._ensure_loaded()
        results = []
        for e in self._entries.values():
            if agent_id and e.agent_id and e.agent_id != agent_id:
                continue  # Different agent -> skip
            results.append(
                CredentialEntry(
                    service=e.service,
                    key=e.key,
                    encrypted=self._fernet is not None,
                    created_at=e.created_at,
                    last_accessed=e.last_accessed,
                )
            )
        return results

    def has(self, service: str, key: str, agent_id: str = "") -> bool:
        """Checks if a credential exists."""
        self._ensure_loaded()
        if agent_id and f"{agent_id}/{service}:{key}" in self._entries:
            return True
        return f"{service}:{key}" in self._entries

    def inject_credentials(self, params: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
        """Injects credentials into tool parameters.

        Called by the gatekeeper, NOT by the planner.

        Args:
            params: The tool parameters.
            mapping: Mapping from param name -> 'service:key'.
                    e.g. {'api_key': 'searxng:api_key'}

        Returns:
            Copy of parameters with injected credentials.
        """
        result = dict(params)
        for param_name, credential_ref in mapping.items():
            parts = credential_ref.split(":", 1)
            if len(parts) != 2:
                continue
            service, key = parts
            value = self.retrieve(service, key)
            if value is not None:
                result[param_name] = value
        return result

    @property
    def count(self) -> int:
        """Number of stored credentials."""
        self._ensure_loaded()
        return len(self._entries)

    @property
    def is_encrypted(self) -> bool:
        """True if real encryption is active."""
        return self._fernet is not None and _HAS_CRYPTO

    # ========================================================================
    # Private Methods
    # ========================================================================

    def _encrypt(self, plaintext: str) -> str:
        """Encrypts a plaintext value."""
        if not self._fernet:
            raise RuntimeError(
                "cryptography-Paket erforderlich für Credential-Verschlüsselung. "
                "pip install cryptography"
            )
        return self._fernet.encrypt(plaintext.encode()).decode()  # type: ignore[no-any-return]

    def _decrypt(self, ciphertext: str) -> str | None:
        """Decrypts an encrypted value."""
        try:
            if not self._fernet:
                raise RuntimeError(
                    "cryptography package required for credential decryption. "
                    "pip install cryptography"
                )
            return self._fernet.decrypt(ciphertext.encode()).decode()  # type: ignore[no-any-return]
        except Exception as exc:
            # Ciphertext prefix for debugging (first 8 chars, no secrets exposed)
            preview = ciphertext[:8] + "..." if len(ciphertext) > 8 else ciphertext
            log.warning(
                "credential_decrypt_failed",
                error=str(exc),
                ciphertext_preview=preview,
            )
            return None

    def _ensure_loaded(self) -> None:
        """Loads the store from disk if needed."""
        if self._loaded:
            return
        if self._store_path.exists():
            try:
                raw = self._store_path.read_text(encoding="utf-8").strip()
                if not raw:
                    # Empty file — treat as fresh store
                    self._loaded = True
                    return
                data = json.loads(raw)
                for lookup, entry_data in data.items():
                    self._entries[lookup] = _StoredCredential(
                        service=entry_data["service"],
                        key=entry_data["key"],
                        encrypted_value=entry_data["encrypted_value"],
                        created_at=datetime.fromisoformat(
                            entry_data.get("created_at", "2025-01-01T00:00:00+00:00")
                        ),
                        last_accessed=(
                            datetime.fromisoformat(entry_data["last_accessed"])
                            if entry_data.get("last_accessed")
                            else None
                        ),
                        agent_id=entry_data.get("agent_id", ""),
                    )
            except (json.JSONDecodeError, KeyError, OSError) as exc:
                log.error("credential_store_load_failed", error=str(exc))
        self._loaded = True

    def _save(self) -> None:
        """Saves the store to disk."""
        data: dict[str, Any] = {}
        for lookup, entry in self._entries.items():
            data[lookup] = {
                "service": entry.service,
                "key": entry.key,
                "encrypted_value": entry.encrypted_value,
                "created_at": entry.created_at.isoformat(),
                "last_accessed": (entry.last_accessed.isoformat() if entry.last_accessed else None),
                "agent_id": entry.agent_id,
            }
        raw = json.dumps(data, ensure_ascii=False, indent=2)
        # Atomic write: write to temp file first, then rename
        tmp_path = self._store_path.with_suffix(".tmp")
        tmp_path.write_text(raw, encoding="utf-8")
        self._set_file_permissions(tmp_path)
        tmp_path.replace(self._store_path)

    @staticmethod
    def _set_file_permissions(path: Path) -> None:
        """Sets file permissions to owner-only (0600)."""
        try:
            path.chmod(stat.S_IRUSR | stat.S_IWUSR)
        except OSError as exc:
            log.warning(
                "credential_chmod_failed",
                path=str(path),
                error=str(exc),
            )


class _StoredCredential:
    """Internal storage format for credentials."""

    __slots__ = (
        "agent_id",
        "created_at",
        "encrypted_value",
        "key",
        "last_accessed",
        "service",
    )

    def __init__(
        self,
        service: str,
        key: str,
        encrypted_value: str,
        created_at: datetime | None = None,
        last_accessed: datetime | None = None,
        agent_id: str = "",
    ) -> None:
        self.service = service
        self.key = key
        self.encrypted_value = encrypted_value
        self.created_at = created_at or datetime.now(UTC)
        self.last_accessed = last_accessed
        self.agent_id = agent_id
