"""W13 · Credential Broker · agente NUNCA recibe token."""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any, Callable


class CredentialDenied(Exception):
    pass


@dataclass
class TemporaryCredential:
    handle: str
    scope: tuple[str, ...]
    repo: str
    expires_at: float
    issued_to: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "handle": self.handle,
            "scope": list(self.scope),
            "repo": self.repo,
            "expires_at": self.expires_at,
            "issued_to": self.issued_to,
        }


class CredentialBroker:
    def __init__(
        self,
        *,
        ttl_seconds: int = 900,
        secret_provider: Callable[..., str] | None = None,
    ) -> None:
        self.ttl_seconds = ttl_seconds
        self._secret_provider = secret_provider
        self._issued: dict[str, TemporaryCredential] = {}
        self._secrets: dict[str, str] = {}

    def issue(
        self,
        *,
        repo: str,
        scopes: list[str] | tuple[str, ...],
        issued_to: str = "github_gateway",
        agent_id: str | None = None,
    ) -> TemporaryCredential:
        if agent_id:
            raise CredentialDenied("agent_cannot_receive_credentials")
        if issued_to not in ("github_gateway", "deployment_gateway", "system"):
            raise CredentialDenied("invalid_issuer_target")
        scope = tuple(sorted(set(scopes or ["contents:write"])))
        raw = f"{repo}|{scope}|{time.time()}|{issued_to}"
        handle = "h_" + hashlib.sha256(raw.encode()).hexdigest()[:16]
        secret = ""
        if self._secret_provider:
            secret = str(self._secret_provider(repo=repo, scopes=scope))
        cred = TemporaryCredential(
            handle=handle,
            scope=scope,
            repo=repo,
            expires_at=time.time() + self.ttl_seconds,
            issued_to=issued_to,
        )
        self._issued[handle] = cred
        if secret:
            self._secrets[handle] = secret
        return cred

    def resolve_for_gateway(self, handle: str, *, caller: str) -> str:
        if caller not in ("github_gateway", "deployment_gateway", "system"):
            raise CredentialDenied("resolve_forbidden_for_caller")
        cred = self._issued.get(handle)
        if cred is None:
            raise CredentialDenied("unknown_handle")
        if time.time() > cred.expires_at:
            raise CredentialDenied("credential_expired")
        return self._secrets.get(handle, "")

    def public_view(self, handle: str) -> dict[str, Any] | None:
        c = self._issued.get(handle)
        return c.to_dict() if c else None
