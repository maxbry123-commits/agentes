# -*- coding: utf-8 -*-
"""Wordflow BUILD → publish request — A-DEP-02. 0% LLM."""
from __future__ import annotations

from typing import Any

from .publisher import FakeGitHubPort, run_publish


def build_publish_request(
    *,
    files: list[dict[str, str]],
    repository: str,
    branch: str = "main",
    commit_message: str,
    token_ref: str = "github_token",
    path_prefix: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "token_ref": token_ref,
        "repository": repository,
        "branch": branch,
        "path_prefix": path_prefix,
        "files": [
            {
                "source": f.get("source") or f.get("path") or "",
                "destination": f.get("destination") or f.get("path") or "",
                "content": f.get("content"),
            }
            for f in files
        ],
        "commit_message": commit_message,
    }


def publish_from_build(
    *,
    files: list[dict[str, str]],
    repository: str,
    commit_message: str,
    credential_store: dict[str, str],
    branch: str = "main",
    token_ref: str = "github_token",
    path_prefix: str = "",
    port: Any = None,
) -> dict[str, Any]:
    req = build_publish_request(
        files=files,
        repository=repository,
        branch=branch,
        commit_message=commit_message,
        token_ref=token_ref,
        path_prefix=path_prefix,
    )
    return run_publish(
        req,
        port=port or FakeGitHubPort(),
        credential_store=credential_store,
    )
