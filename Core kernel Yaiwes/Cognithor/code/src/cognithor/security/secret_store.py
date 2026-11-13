"""SecretStore: Moves API keys from config.yaml to OS Keyring.

Keeps plaintext secrets out of config files by storing them in the
OS-native credential store (Keychain on macOS, Credential Manager on
Windows, libsecret on Linux).

Usage::

    from cognithor.security.secret_store import SecretStore

    store = SecretStore()
    if store.is_available:
        store.store("openai_api_key", "sk-proj-...")
        key = store.retrieve("openai_api_key")

Migration::

    migrated = store.migrate_from_config(Path.home() / ".cognithor" / "config.yaml")
    # config.yaml: openai_api_key is now ''
    # keyring:     openai_api_key -> "sk-proj-..."
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from cognithor.utils.logging import get_logger

log = get_logger(__name__)

__all__ = ["SecretStore"]

# The service name used in OS Keyring
_SERVICE = "cognithor-secrets"

# Sentinel stored in the index entry so we can enumerate keys later.
# (keyring has no native list-all-passwords API on all backends.)
_INDEX_KEY = "__key_index__"

# Field name patterns that are considered secrets
_SECRET_FIELD_RE = re.compile(
    r"^("
    r".*_api_key"
    r"|.*_token"
    r"|.*_secret"
    r"|.*_password"
    r")$",
    re.IGNORECASE,
)

# Fields to skip even if they match the pattern (known non-secrets)
_SKIP_FIELDS = frozenset(
    {
        # lmstudio_api_key is always a dummy value ("lm-studio")
        "lmstudio_api_key",
        # arc arc_api_key_env is just an env-var name, not the key itself
        "api_key_env",
        # internal gatekeeper pattern strings
        "contains_pattern",
    }
)

# Local API keys that are not real secrets
_LOCAL_API_KEYS = frozenset(
    {
        "lmstudio_api_key",
        "vllm_api_key",
        "llama_cpp_api_key",
    }
)


class SecretStore:
    """Stores API keys in OS Keyring instead of plaintext config files.

    All operations are non-throwing: failures are logged and a safe
    fallback value is returned so callers never crash.
    """

    SERVICE = _SERVICE

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _keyring_available(self) -> bool:
        try:
            import keyring  # noqa: F401

            return True
        except ImportError:
            return False

    @property
    def is_available(self) -> bool:
        """True if the keyring backend is usable."""
        return self._keyring_available()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def store(self, key_name: str, value: str) -> bool:
        """Store a secret in OS Keyring.

        Args:
            key_name: Logical name (e.g. ``"openai_api_key"``).
            value:    The secret value to store.

        Returns:
            True on success, False if keyring is unavailable or errored.
        """
        if not value:
            return False
        try:
            import keyring

            keyring.set_password(_SERVICE, key_name, value)
            self._add_to_index(key_name)
            log.debug("secret_stored", key=key_name)
            return True
        except Exception as exc:
            log.warning("secret_store_failed", key=key_name, error=str(exc)[:80])
            return False

    def retrieve(self, key_name: str) -> str:
        """Retrieve a secret from OS Keyring.

        Returns:
            The stored value, or ``''`` if not found / unavailable.
        """
        try:
            import keyring

            value = keyring.get_password(_SERVICE, key_name)
            return value or ""
        except Exception as exc:
            log.debug("secret_retrieve_failed", key=key_name, error=str(exc)[:80])
            return ""

    def delete(self, key_name: str) -> bool:
        """Remove a secret from OS Keyring.

        Returns:
            True on success, False if not found / unavailable.
        """
        try:
            import keyring

            keyring.delete_password(_SERVICE, key_name)
            self._remove_from_index(key_name)
            return True
        except Exception as exc:
            log.debug("secret_delete_failed", key=key_name, error=str(exc)[:80])
            return False

    def list_keys(self) -> list[str]:
        """List all secret names currently stored under this service.

        Returns:
            Sorted list of key names.  Empty list if keyring unavailable.
        """
        raw = self.retrieve(_INDEX_KEY)
        if not raw:
            return []
        return sorted(k.strip() for k in raw.split(",") if k.strip())

    # ------------------------------------------------------------------ #
    # Migration helpers
    # ------------------------------------------------------------------ #

    def migrate_from_config(self, config_path: Path) -> int:
        """Move API keys from config.yaml to keyring.

        For every field that:
        - matches ``_SECRET_FIELD_RE`` (e.g. ``openai_api_key``, ``twitch_token``)
        - has a non-empty, non-placeholder value
        - is not in ``_SKIP_FIELDS`` / ``_LOCAL_API_KEYS``

        the value is stored in keyring and the field in config.yaml is
        replaced with an empty string (``''``).

        The method is **idempotent**: if a key is already empty in the
        config file (already migrated), it is silently skipped.

        Args:
            config_path: Path to config.yaml.

        Returns:
            Number of secrets migrated this call (0 if none needed).
        """
        if not self.is_available:
            log.debug("secret_migrate_skip_no_keyring")
            return 0

        config_path = Path(config_path)
        if not config_path.exists():
            return 0

        try:
            with open(config_path, encoding="utf-8") as f:
                original = f.read()
        except OSError as exc:
            log.warning("secret_migrate_read_failed", path=str(config_path), error=str(exc)[:80])
            return 0

        lines = original.splitlines(keepends=True)
        migrated = 0
        new_lines: list[str] = []

        for line in lines:
            replacement = self._maybe_migrate_line(line)
            if replacement is not None:
                new_lines.append(replacement)
                migrated += 1
            else:
                new_lines.append(line)

        if migrated == 0:
            return 0

        new_content = "".join(new_lines)
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            log.info("secret_migrate_done", count=migrated, config=str(config_path)[-60:])
        except OSError as exc:
            log.error("secret_migrate_write_failed", path=str(config_path), error=str(exc)[:80])
            return 0

        return migrated

    def migrate_from_env(self, env_path: Path) -> int:
        """Move secrets from a .env file to keyring, leaving non-secret vars.

        Lines matching ``KEY=value`` where KEY looks like a secret are
        moved to keyring and replaced with ``KEY=`` in the file.

        Args:
            env_path: Path to the .env file.

        Returns:
            Number of secrets migrated.
        """
        if not self.is_available:
            return 0

        env_path = Path(env_path)
        if not env_path.exists():
            return 0

        try:
            with open(env_path, encoding="utf-8") as f:
                original = f.read()
        except OSError:
            return 0

        migrated = 0
        new_lines: list[str] = []

        for line in original.splitlines(keepends=True):
            stripped = line.rstrip("\n\r")
            if stripped.startswith("#") or "=" not in stripped:
                new_lines.append(line)
                continue

            key_part, _, val_part = stripped.partition("=")
            key_part = key_part.strip()
            val_part = val_part.strip().strip('"').strip("'")

            if (
                _SECRET_FIELD_RE.match(key_part)
                and key_part not in _SKIP_FIELDS
                and val_part
                and val_part not in ("", '""', "''")
                and self.store(key_part, val_part)
            ):
                eol = line[len(stripped) :]
                new_lines.append(f"{key_part}={eol}")
                migrated += 1
                continue

            new_lines.append(line)

        if migrated == 0:
            return 0

        try:
            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            log.info("secret_migrate_env_done", count=migrated, path=str(env_path)[-60:])
        except OSError as exc:
            log.error("secret_migrate_env_write_failed", error=str(exc)[:80])
            return 0

        return migrated

    # ------------------------------------------------------------------ #
    # Private
    # ------------------------------------------------------------------ #

    def _maybe_migrate_line(self, line: str) -> str | None:
        """Return replacement line if line contains a migratable secret.

        Returns None if no migration needed (keep original line).
        The replacement clears the value to ``''``.
        """
        # Match YAML lines like:  openai_api_key: sk-proj-...
        # Allow optional leading spaces (nested YAML)
        m = re.match(
            r"^(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.+)$",
            line.rstrip("\n\r"),
        )
        if not m:
            return None

        indent, field_name, raw_value = m.group(1), m.group(2), m.group(3)

        # Skip comments, non-secret fields, local keys, placeholder values
        if not _SECRET_FIELD_RE.match(field_name):
            return None
        if field_name in _SKIP_FIELDS or field_name in _LOCAL_API_KEYS:
            return None

        # Strip quotes and whitespace
        value = raw_value.strip().strip('"').strip("'")

        # Skip empty / already-cleared / placeholder values
        if not value or value in ("''", '""', "~", "null"):
            return None
        # Skip obvious non-secret placeholders
        if value.startswith("lm-studio") or value == "***":
            return None

        # Store in keyring; only clear the line if storage succeeded
        if self.store(field_name, value):
            eol = "\n" if line.endswith("\n") else ""
            return f"{indent}{field_name}: ''{eol}"

        return None

    def _add_to_index(self, key_name: str) -> None:
        """Maintain a comma-separated index of stored key names."""
        if key_name == _INDEX_KEY:
            return
        current = self.retrieve(_INDEX_KEY)
        keys = {k.strip() for k in current.split(",") if k.strip()}
        keys.add(key_name)
        try:
            import keyring

            keyring.set_password(_SERVICE, _INDEX_KEY, ",".join(sorted(keys)))
        except Exception:
            log.debug("secret_store_index_update_failed", exc_info=True)

    def _remove_from_index(self, key_name: str) -> None:
        """Remove a key name from the index."""
        current = self.retrieve(_INDEX_KEY)
        keys = {k.strip() for k in current.split(",") if k.strip()}
        keys.discard(key_name)
        try:
            import keyring

            keyring.set_password(_SERVICE, _INDEX_KEY, ",".join(sorted(keys)))
        except Exception:
            log.debug("secret_store_index_remove_failed", exc_info=True)

    # ------------------------------------------------------------------ #
    # Convenience: dump stored secrets (for debugging, never in prod logs)
    # ------------------------------------------------------------------ #

    def dump(self) -> dict[str, Any]:
        """Return a dict of {key: masked_value} for debugging.

        Values are always masked — this is safe to log.
        """
        result: dict[str, Any] = {}
        for k in self.list_keys():
            v = self.retrieve(k)
            result[k] = ("***" + v[-4:]) if len(v) > 4 else "***"
        return result
