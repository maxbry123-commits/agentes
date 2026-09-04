"""T38 — require AccountRegistry.get before publish. No secrets in logs."""
from __future__ import annotations
from typing import Any
class AccountRequired(ValueError): pass
def require_account(registry: Any, account_id: str | None) -> Any:
    if not account_id: raise AccountRequired("account_id required")
    getter = getattr(registry, "get", None); acc = getter(account_id) if callable(getter) else None
    if acc is None: raise AccountRequired(f"account not found: {account_id}")
    return acc
def publish_with_account(registry: Any, account_id: str | None, payload: dict | None = None) -> dict:
    acc = require_account(registry, account_id); aid = getattr(acc, "account_id", account_id)
    return {"ok": True, "account_id": aid, "published": False, "mode": "dry"}
