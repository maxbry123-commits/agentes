# -*- coding: utf-8 -*-
"""C-10 GitHub Deploy — Wordflow-controlled publish. 0% LLM.

Does not force_push. Requires expected_head when configured.
Token only via token_ref. Protected paths blocked.
"""
from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

from extensions.wordflow.engine.github_publisher import (
    DryRunExecutor,
    GitHubPublisher,
    MapCredentialStore,
    validate_contract,
)

DEFAULT_PROTECTED = [
    ".github/workflows/**",
    "**/secrets/**",
    "**/*credential*",
    "**/*token*",
]


class DeployError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def load_deploy_config(path: str | Path | None = None) -> dict[str, Any]:
    cfg = {
        "force_push": False,
        "require_expected_head": True,
        "dry_run_default": True,
        "protected_patterns": list(DEFAULT_PROTECTED),
        "llm_control": "DENY",
    }
    if path is None:
        path = Path(__file__).with_name("deploy_config.yaml")
    p = Path(path)
    if p.is_file() and yaml is not None:
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        if isinstance(data, dict):
            cfg.update({k: v for k, v in data.items() if k in cfg or k == "protected_patterns"})
            if "protected_patterns" in data:
                cfg["protected_patterns"] = list(data["protected_patterns"])
    return cfg


def _is_protected(dest: str, patterns: list[str]) -> bool:
    for pat in patterns:
        if fnmatch.fnmatch(dest, pat):
            return True
    return False


class FakeGitDataPort:
    """In-memory port: blob→tree→commit→ref simulation."""

    def __init__(self, head_sha: str = "0" * 40):
        self.head_sha = head_sha
        self.commits: list[dict[str, Any]] = []

    def current_head(self, repository: str, branch: str) -> str:
        return self.head_sha

    def publish(self, plan: dict[str, Any], token: str) -> dict[str, Any]:
        if not token:
            return {"ok": False, "reason": "NO_TOKEN"}
        new_sha = f"c{len(self.commits):039d}"[-40:]
        self.commits.append({"plan": plan, "sha": new_sha})
        self.head_sha = new_sha
        return {
            "ok": True,
            "mode": "fake_git_data",
            "commit_sha": new_sha,
            "files": len(plan.get("files") or []),
            "repository": plan.get("repository"),
            "branch": plan.get("branch"),
        }


class GitHubDeployer:
    def __init__(
        self,
        *,
        config: dict[str, Any] | None = None,
        credentials: Any | None = None,
        port: Any | None = None,
        dry_run: bool | None = None,
    ):
        self.config = config or load_deploy_config()
        self.credentials = credentials or MapCredentialStore()
        use_dry = self.config.get("dry_run_default", True) if dry_run is None else dry_run
        self.port = port or (DryRunExecutor() if use_dry else FakeGitDataPort())
        self.publisher = GitHubPublisher(credentials=self.credentials, executor=self.port)

    def deploy(self, contract: dict[str, Any]) -> dict[str, Any]:
        v = validate_contract(contract)
        if not v.get("ok"):
            return {**v, "llm_control": "DENY"}

        if contract.get("force_push") and not self.config.get("force_push", False):
            return {"ok": False, "reason": "FORCE_PUSH_DENIED", "llm_control": "DENY"}

        patterns = list(self.config.get("protected_patterns") or DEFAULT_PROTECTED)
        blocked = []
        for f in contract.get("files") or []:
            dest = str(f.get("destination") or "")
            if _is_protected(dest, patterns):
                blocked.append(dest)
        if blocked:
            return {
                "ok": False,
                "reason": "PROTECTED_PATH",
                "blocked": blocked,
                "llm_control": "DENY",
            }

        if self.config.get("require_expected_head", True):
            expected = contract.get("expected_head")
            if not expected:
                return {"ok": False, "reason": "MISSING_EXPECTED_HEAD", "llm_control": "DENY"}
            if hasattr(self.port, "current_head"):
                head = self.port.current_head(contract["repository"], contract["branch"])
                if head != expected:
                    return {
                        "ok": False,
                        "reason": "HEAD_CONFLICT",
                        "expected_head": expected,
                        "actual_head": head,
                        "llm_control": "DENY",
                    }

        result = self.publisher.publish(contract)
        result["llm_control"] = "DENY"
        if result.get("ok"):
            result["evidence"] = {
                "repository": contract["repository"],
                "branch": contract["branch"],
                "files": [f.get("destination") for f in contract.get("files") or []],
                "commit_message": contract.get("commit_message"),
            }
        return result
