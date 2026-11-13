"""Workspace → repository → account_id resolution. Fail closed on mismatch."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Literal
from .registry import AccountRegistry, AccountRecord
Decision = Literal["ALLOW", "DENY"]
@dataclass(frozen=True)
class WorkspaceRepo:
    workspace_id: str; provider: str; owner: str; repo: str; account_id: str | None = None; branch: str = "main"
    @property
    def full_name(self) -> str: return f"{self.owner}/{self.repo}"
@dataclass
class ResolveResult:
    decision: Decision; account: AccountRecord | None = None; reason: str = ""; credential_ref: str | None = None; detail: dict[str, Any] = field(default_factory=dict)
class AccountResolver:
    def __init__(self, registry: AccountRegistry): self.registry = registry
    def resolve(self, workspace_repo: WorkspaceRepo, need_write: bool = False, need_deploy: bool = False) -> ResolveResult:
        account_id = workspace_repo.account_id
        if account_id:
            acc = self.registry.get(account_id)
            if acc is None: return ResolveResult("DENY", reason="account_not_registered", detail={"account_id": account_id})
            return self._check(acc, workspace_repo, need_write, need_deploy)
        candidates = self.registry.find_for_repo(workspace_repo.full_name, workspace_repo.provider)
        if not candidates: return ResolveResult("DENY", reason="no_account_for_repo", detail={"repo": workspace_repo.full_name})
        exact = [c for c in candidates if workspace_repo.full_name in c.allowed_repositories]; acc = exact[0] if exact else candidates[0]
        return self._check(acc, workspace_repo, need_write, need_deploy)
    def _check(self, acc: AccountRecord, workspace_repo: WorkspaceRepo, need_write: bool, need_deploy: bool) -> ResolveResult:
        if acc.provider != workspace_repo.provider: return ResolveResult("DENY", account=acc, reason="provider_mismatch")
        if acc.allowed_repositories and workspace_repo.full_name not in acc.allowed_repositories: return ResolveResult("DENY", account=acc, reason="repository_not_allowed")
        pol = acc.policy or {}
        if need_write and not pol.get("can_write", False): return ResolveResult("DENY", account=acc, reason="policy_can_write_false")
        if need_deploy and not pol.get("can_deploy", False): return ResolveResult("DENY", account=acc, reason="policy_can_deploy_false")
        return ResolveResult("ALLOW", account=acc, reason="ok", credential_ref=acc.credential_ref, detail={"account_id": acc.account_id, "branch": workspace_repo.branch or acc.default_branch})
