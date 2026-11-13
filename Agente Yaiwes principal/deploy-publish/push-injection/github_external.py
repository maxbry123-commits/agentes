# -*- coding: utf-8 -*-
"""GitHub external account connector (Cuenta B — software store).

Reads repos on another GitHub account/org for download/metadata.
Does NOT execute remote code. Tokens only via credential_ref / env.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class ExternalGitHubConfig:
    owner: str
    repo: str
    branch: str = "main"
    credential_ref: str = ""


class CredentialResolutionError(RuntimeError):
    pass


def resolve_credential(credential_ref: str) -> str:
    """Resolve credential_ref to token string. Never log the value."""
    if not credential_ref:
        raise CredentialResolutionError("credential_ref empty")
    if credential_ref.startswith("ghp_") or credential_ref.startswith("github_pat_"):
        raise CredentialResolutionError("raw token forbidden; use env:NAME or secret://...")
    if credential_ref.startswith("env:"):
        key = credential_ref[4:]
        val = os.environ.get(key, "")
        if not val:
            raise CredentialResolutionError(f"env not set: {key}")
        return val
    val = os.environ.get(credential_ref, "")
    if not val:
        raise CredentialResolutionError(
            f"unresolved credential_ref={credential_ref!r}; set env or secret store"
        )
    return val


@dataclass
class ExternalFileMeta:
    path: str
    sha: str
    size: int
    download_url: Optional[str]
    content: Optional[bytes]


class GitHubExternalConnector:
    """Cuenta B access via PyGithub if available; otherwise metadata-only stub."""

    def __init__(self, config: ExternalGitHubConfig) -> None:
        self.config = config
        self._token: Optional[str] = None

    def _token_resolved(self) -> str:
        if self._token is None:
            self._token = resolve_credential(self.config.credential_ref)
        return self._token

    def connect(self) -> Any:
        """Return PyGithub repo object or raise if library/token missing."""
        try:
            from github import Github  # type: ignore
        except ImportError as e:
            raise RuntimeError("PyGithub not installed; pip install PyGithub") from e
        gh = Github(self._token_resolved())
        repo = gh.get_repo(f"{self.config.owner}/{self.config.repo}")
        repo.get_branch(self.config.branch)
        return repo

    def get_file(self, path: str, with_content: bool = True) -> ExternalFileMeta:
        repo = self.connect()
        file = repo.get_contents(path, ref=self.config.branch)
        if isinstance(file, list):
            raise IsADirectoryError(path)
        content = file.decoded_content if with_content else None
        return ExternalFileMeta(
            path=file.path,
            sha=file.sha,
            size=file.size,
            download_url=file.download_url,
            content=content,
        )

    def preflight_repo(self) -> dict[str, Any]:
        repo = self.connect()
        return {
            "full_name": repo.full_name,
            "default_branch": repo.default_branch,
            "requested_branch": self.config.branch,
            "private": bool(repo.private),
            "ok": True,
        }


def config_from_mapping(data: dict[str, Any]) -> ExternalGitHubConfig:
    return ExternalGitHubConfig(
        owner=str(data["owner"]),
        repo=str(data["repo"]),
        branch=str(data.get("branch", "main")),
        credential_ref=str(data["credential_ref"]),
    )
