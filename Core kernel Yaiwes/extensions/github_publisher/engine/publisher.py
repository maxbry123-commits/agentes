# -*- coding: utf-8 -*-
"""GitHub Publisher — A-DEP-01. token_ref only. 0% LLM."""
from __future__ import annotations

import re
from typing import Any, Protocol

REPO_RE = re.compile(r"^[\w.-]+/[\w.-]+$")
SECRET_RE = re.compile(r"(ghp_|github_pat_|token\s*=)", re.IGNORECASE)


class PublishError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


class GitHubPort(Protocol):
    def create_commit(
        self,
        *,
        repository: str,
        branch: str,
        files: list[dict[str, str]],
        message: str,
        token: str,
    ) -> dict[str, Any]: ...


def normalize_publish(raw: dict[str, Any] | None) -> dict[str, Any]:
    if raw is None or not isinstance(raw, dict):
        raise PublishError("MISSING_PUBLISH")
    if raw.get("schema_version") != "1.0":
        raise PublishError("INVALID_SCHEMA", "schema_version")

    token_ref = raw.get("token_ref")
    if not token_ref or not isinstance(token_ref, str):
        raise PublishError("MISSING_TOKEN_REF")
    if raw.get("token") or raw.get("github_token"):
        raise PublishError("RAW_TOKEN_FORBIDDEN")
    if SECRET_RE.search(token_ref) or token_ref.startswith("ghp_"):
        raise PublishError("TOKEN_REF_LOOKS_LIKE_SECRET")

    repo = raw.get("repository")
    if not repo or not REPO_RE.match(str(repo)):
        raise PublishError("INVALID_REPOSITORY", str(repo))

    branch = raw.get("branch") or "main"
    message = raw.get("commit_message")
    if not message:
        raise PublishError("MISSING_COMMIT_MESSAGE")

    files = raw.get("files")
    if not isinstance(files, list) or len(files) == 0:
        raise PublishError("MISSING_FILES")
    norm_files = []
    for f in files:
        if not isinstance(f, dict) or not f.get("source") or not f.get("destination"):
            raise PublishError("INVALID_FILE_ENTRY")
        if SECRET_RE.search(str(f.get("content") or "")):
            raise PublishError("SECRET_IN_CONTENT", f.get("destination"))
        norm_files.append({
            "source": f["source"],
            "destination": f["destination"],
            "content": f.get("content"),
        })

    return {
        "schema_version": "1.0",
        "token_ref": token_ref,
        "repository": repo,
        "branch": branch,
        "path_prefix": raw.get("path_prefix") or "",
        "files": norm_files,
        "commit_message": message,
        "llm_control": "DENY",
    }


def resolve_token(token_ref: str, store: dict[str, str] | None) -> str:
    if not store or token_ref not in store:
        raise PublishError("TOKEN_REF_NOT_FOUND", token_ref)
    token = store[token_ref]
    if not token:
        raise PublishError("TOKEN_EMPTY", token_ref)
    return token


def run_publish(
    raw: dict[str, Any] | None,
    *,
    port: GitHubPort,
    credential_store: dict[str, str] | None = None,
) -> dict[str, Any]:
    try:
        req = normalize_publish(raw)
        token = resolve_token(req["token_ref"], credential_store)
    except PublishError as e:
        return {
            "ok": False,
            "status": "FAILED",
            "reason": e.reason_code,
            "detail": e.detail,
        }

    files_payload = []
    prefix = req["path_prefix"]
    for f in req["files"]:
        dest = f["destination"]
        if prefix and not dest.startswith(prefix):
            dest = f"{prefix.rstrip('/')}/{dest}"
        content = f.get("content")
        if content is None:
            content = f"[FROM_SOURCE:{f['source']}]"
        files_payload.append({"path": dest, "content": content})

    try:
        result = port.create_commit(
            repository=req["repository"],
            branch=req["branch"],
            files=files_payload,
            message=req["commit_message"],
            token=token,
        )
    except Exception as e:
        return {
            "ok": False,
            "status": "FAILED",
            "reason": "PORT_ERROR",
            "detail": str(e)[:200],
        }

    return {
        "ok": True,
        "status": "SUCCESS",
        "repository": req["repository"],
        "branch": req["branch"],
        "commit_sha": result.get("commit_sha"),
        "files_count": len(files_payload),
        "token_ref": req["token_ref"],
        "llm_control": "DENY",
    }


class FakeGitHubPort:
    def __init__(self):
        self.commits: list[dict[str, Any]] = []

    def create_commit(
        self,
        *,
        repository: str,
        branch: str,
        files: list[dict[str, str]],
        message: str,
        token: str,
    ) -> dict[str, Any]:
        if not token:
            raise RuntimeError("empty token")
        sha = f"fake{len(self.commits):040d}"[:40]
        rec = {
            "repository": repository,
            "branch": branch,
            "message": message,
            "files": [{"path": f["path"]} for f in files],
            "commit_sha": sha,
        }
        self.commits.append(rec)
        return rec
