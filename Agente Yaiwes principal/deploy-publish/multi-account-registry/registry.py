"""AccountRegistry — multi GitHub (and provider) accounts.

credential_ref only — never store raw tokens in registry or workflow body.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any

@dataclass
class AccountRecord:
    account_id: str
    provider: str
    credential_ref: str
    allowed_repositories: tuple[str, ...] = ()
    default_branch: str = "main"
    policy: dict[str, Any] = field(default_factory=lambda: {"can_read": True, "can_write": True, "can_deploy": False})
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]: return asdict(self)

class AccountRegistry:
    def __init__(self) -> None: self._accounts: dict[str, AccountRecord] = {}
    def register(self, account: AccountRecord) -> None:
        if account.account_id in self._accounts: raise ValueError(f"account already registered: {account.account_id}")
        if not account.credential_ref: raise ValueError("credential_ref required")
        if account.credential_ref.startswith("ghp_") or "token" in account.credential_ref.lower() and account.credential_ref.startswith("gh"):
            if account.credential_ref.startswith("ghp_") or account.credential_ref.startswith("github_pat_"): raise ValueError("raw token forbidden; use credential_ref")
        self._accounts[account.account_id] = account
    def get(self, account_id: str) -> AccountRecord | None: return self._accounts.get(account_id)
    def list_ids(self) -> list[str]: return sorted(self._accounts.keys())
    def find_for_repo(self, repo_full_name: str, provider: str = "github") -> list[AccountRecord]:
        return [a for a in self._accounts.values() if a.provider == provider and (not a.allowed_repositories or repo_full_name in a.allowed_repositories)]
