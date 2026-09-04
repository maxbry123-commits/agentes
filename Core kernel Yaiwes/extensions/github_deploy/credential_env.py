"""Resolve credential_ref → token. Never log the secret."""
from __future__ import annotations

import os
from typing import Any


class CredentialUnresolved(ValueError):
    pass


def is_raw_pat(value: str) -> bool:
    v = str(value or "")
    return v.startswith("ghp_") or v.startswith("github_pat_") or v.startswith("hf_")


def resolve_token(token_ref: str, extra: dict[str, str] | None = None) -> str:
    ref = str(token_ref or "").strip()
    if not ref:
        raise CredentialUnresolved("token_ref empty")
    if is_raw_pat(ref):
        raise CredentialUnresolved("raw token forbidden; use env:NAME or secret://...")
    if extra and ref in extra:
        val = extra[ref]
        if not val:
            raise CredentialUnresolved("extra mapping empty")
        return val
    if ref.startswith("env:"):
        key = ref[4:]
        val = os.environ.get(key, "")
        if not val:
            raise CredentialUnresolved(f"env not set: {key}")
        return val
    if ref.startswith("secret://"):
        key = "WF_SECRET_" + ref[9:].replace("/", "_").upper()
        val = os.environ.get(key, "") or os.environ.get(ref, "")
        if not val:
            raise CredentialUnresolved(f"secret unresolved: {ref}")
        return val
    val = os.environ.get(ref, "")
    if not val:
        raise CredentialUnresolved(f"unresolved token_ref={ref!r}")
    return val


class EnvCredentialStore:
    def __init__(self, extra: dict[str, str] | None = None):
        self._extra = dict(extra or {})

    def resolve(self, token_ref: str) -> str | None:
        try:
            return resolve_token(token_ref, self._extra)
        except CredentialUnresolved:
            return None


def redact(obj: Any) -> Any:
    from extensions.github_deploy.token_ref import redact_logs

    if isinstance(obj, str):
        return redact_logs(obj)
    if isinstance(obj, dict):
        # Drop only secret token keys; keep file content (needed by remote_ops read/verify).
        return {k: redact(v) for k, v in obj.items() if k != "token"}
    if isinstance(obj, list):
        return [redact(x) for x in obj]
    return obj
