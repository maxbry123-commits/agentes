# -*- coding: utf-8 -*-
"""C-18 CredentialStore — token_ref resolution only. 0% LLM."""
from __future__ import annotations

import os
import re
from typing import Any, Protocol

_INLINE = re.compile(r"(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|hf_[A-Za-z0-9]{20,})")


class CredentialError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


class CredentialStore(Protocol):
    def resolve(self, token_ref: str) -> str | None: ...


class MapCredentialStore:
    def __init__(self, mapping: dict[str, str] | None = None):
        self._m = dict(mapping or {})

    def resolve(self, token_ref: str) -> str | None:
        return self._m.get(token_ref)

    def put(self, token_ref: str, value: str) -> None:
        if not token_ref:
            raise CredentialError("TOKEN_REF_EMPTY")
        if not value:
            raise CredentialError("TOKEN_VALUE_EMPTY")
        self._m[token_ref] = value


class EnvCredentialStore:
    """Resolves token_ref as environment variable name."""

    def resolve(self, token_ref: str) -> str | None:
        if not token_ref:
            return None
        return os.environ.get(token_ref)


def assert_no_inline_secrets(payload: Any) -> dict[str, Any]:
    blob = str(payload)
    if _INLINE.search(blob):
        raise CredentialError("INLINE_SECRET_FORBIDDEN")
    return {"ok": True, "llm_control": "DENY"}


def resolve_required(store: CredentialStore, token_ref: str) -> str:
    if not token_ref:
        raise CredentialError("TOKEN_REF_EMPTY")
    val = store.resolve(token_ref)
    if not val:
        raise CredentialError("TOKEN_REF_UNRESOLVED", token_ref)
    return val
