"""Write 9Router's credential db for one cloud run, without a refresh token. Ever.

This container must be structurally incapable of rotating the user's OAuth grant.
9Router's refresh dispatcher bails on `if (!b || !b.refreshToken) return null`, so a
providerConnections entry with no such field is one it can spend and never rotate.
If the runner did rotate, the user's laptop would be left replaying a dead token and
the provider would revoke their entire grant family. That is the whole safety
property of this file, not a style preference.

Two independent walls hold it up:
  1. ProviderCredential forbids extra fields, so a payload carrying `refreshToken`
     never parses into the process at all.
  2. assert_no_refresh_token re-reads the assembled payload just before the write
     and refuses anything whose key names a refresh token, however it got there.
"""

import json
import os
import tempfile
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from typeguard import typechecked

from runner.run_spec import ProviderCredential

DB_FILENAME = "db.json"

# Normalized key fragment that must never appear anywhere in the db we write.
FORBIDDEN_KEY_FRAGMENT = "refreshtoken"


class RefreshTokenLeak(RuntimeError):
    """A refresh token reached the credential writer. Fail the run rather than write it."""


@typechecked
def p_normalize_key(key: str) -> str:
    return "".join(char for char in key.lower() if char.isalnum())


@typechecked
def p_iso(moment: datetime) -> str:
    """9Router timestamps are ISO-8601 UTC with a Z suffix; match it exactly."""
    return moment.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


@typechecked
def assert_no_refresh_token(payload: Any, path: str = "$") -> None:
    """Raise if any key anywhere under `payload` names a refresh token."""
    if isinstance(payload, dict):
        for key, value in payload.items():
            if FORBIDDEN_KEY_FRAGMENT in p_normalize_key(str(key)):
                raise RefreshTokenLeak(
                    f"refusing to write a 9Router db containing a refresh token at {path}.{key}"
                )
            assert_no_refresh_token(value, f"{path}.{key}")
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            assert_no_refresh_token(value, f"{path}[{index}]")


@typechecked
def router_connection(credential: ProviderCredential, now: datetime) -> Dict[str, Any]:
    """Build one providerConnections entry from an allow-list of keys, never a passthrough."""
    if credential.auth_type != "oauth":
        raise ValueError(f"credential for {credential.provider!r} is not an oauth connection")
    entry: Dict[str, Any] = {
        "id": str(uuid4()),
        "provider": credential.provider,
        "authType": "oauth",
        "name": credential.label,
        "priority": 1,
        "isActive": True,
        "createdAt": p_iso(now),
        "updatedAt": p_iso(now),
        "accessToken": credential.access_token,
        "testStatus": "active",
    }
    if credential.expires_at is not None:
        entry["expiresAt"] = p_iso(credential.expires_at)
    if credential.scope:
        entry["scope"] = credential.scope
    return entry


@typechecked
def router_db_payload(credentials: List[ProviderCredential], now: datetime) -> Dict[str, Any]:
    """A complete 9Router db seeded with this run's subscription connections and nothing else."""
    return {
        "providerConnections": [
            router_connection(credential, now)
            for credential in credentials
            if credential.auth_type == "oauth"
        ],
        "providerNodes": [],
        "proxyPools": [],
        "modelAliases": {},
        "mitmAlias": {},
        "combos": [],
        "apiKeys": [],
        "customModels": [],
        "pricing": {},
        "settings": {},
    }


@typechecked
def write_router_db(data_dir: str, credentials: List[ProviderCredential], now: datetime) -> str:
    """Write $DATA_DIR/db.json owner-only and return its path."""
    payload = router_db_payload(credentials, now)
    assert_no_refresh_token(payload)

    os.makedirs(data_dir, mode=0o700, exist_ok=True)
    os.chmod(data_dir, 0o700)
    path = os.path.join(data_dir, DB_FILENAME)
    handle, temp_path = tempfile.mkstemp(dir=data_dir, prefix=".db-", suffix=".json")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2)
        os.chmod(temp_path, 0o600)
        os.replace(temp_path, path)
    except BaseException:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise
    return path
