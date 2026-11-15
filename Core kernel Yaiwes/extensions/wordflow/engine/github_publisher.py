# -*- coding: utf-8 -*-
"""GitHubPublisher — T34/D4. Deterministic publish contract. 0% LLM.

Token never in workflow body: only token_ref → CredentialStore resolver.
Default mode is dry_run unless GitDataApiExecutor injected.
"""
from __future__ import annotations

from typing import Any, Protocol


class CredentialStore(Protocol):
    def resolve(self, token_ref: str) -> str | None: ...


class MapCredentialStore:
    def __init__(self, mapping: dict[str, str] | None = None):
        self._m = dict(mapping or {})

    def resolve(self, token_ref: str) -> str | None:
        return self._m.get(token_ref)


class DryRunExecutor:
    """Records publish plan; never calls GitHub API."""

    def __init__(self):
        self.calls: list[dict[str, Any]] = []

    def publish(self, plan: dict[str, Any], token: str) -> dict[str, Any]:
        if not token:
            return {"ok": False, "reason": "NO_TOKEN"}
        self.calls.append({k: v for k, v in plan.items() if k != "token"})
        return {
            "ok": True,
            "mode": "dry_run",
            "files": len(plan.get("files") or []),
            "repository": plan.get("repository"),
            "branch": plan.get("branch"),
            "commit_message": plan.get("commit_message"),
        }


def validate_contract(contract: dict[str, Any]) -> dict[str, Any]:
    required = ["token_ref", "repository", "branch", "files", "commit_message"]
    missing = [k for k in required if k not in contract or contract[k] in (None, "", [])]
    if missing:
        return {"ok": False, "reason": "MISSING", "fields": missing}
    if not isinstance(contract["files"], list):
        return {"ok": False, "reason": "FILES_NOT_LIST"}
    for i, f in enumerate(contract["files"]):
        if not isinstance(f, dict) or "source" not in f or "destination" not in f:
            return {"ok": False, "reason": "BAD_FILE_ENTRY", "index": i}
    blob = str(contract)
    if "ghp_" in blob or "github_pat_" in blob:
        return {"ok": False, "reason": "INLINE_TOKEN_FORBIDDEN"}
    return {"ok": True}


class GitHubPublisher:
    def __init__(
        self,
        credentials: CredentialStore | None = None,
        executor: Any | None = None,
    ):
        self.credentials = credentials or MapCredentialStore()
        self.executor = executor or DryRunExecutor()

    def publish(self, contract: dict[str, Any]) -> dict[str, Any]:
        v = validate_contract(contract)
        if not v.get("ok"):
            return v
        token = self.credentials.resolve(str(contract["token_ref"]))
        if not token:
            return {"ok": False, "reason": "TOKEN_REF_UNRESOLVED", "token_ref": contract["token_ref"]}
        plan = {
            "repository": contract["repository"],
            "branch": contract["branch"],
            "path_prefix": contract.get("path_prefix") or "",
            "files": list(contract["files"]),
            "commit_message": contract["commit_message"],
            "content_map": dict(contract.get("content_map") or {}),
        }
        return self.executor.publish(plan, token)
