# -*- coding: utf-8 -*-
"""github_api — D4. Git Data API executor. 0% LLM.

Uses urllib only. Token passed at call time — never logged.
"""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from typing import Any


class GitHubApiError(Exception):
    def __init__(self, status: int, body: str):
        self.status = status
        self.body = body
        super().__init__(f"GitHub API {status}")


def _request(
    method: str,
    url: str,
    token: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = None
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "wordflow-publisher",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise GitHubApiError(e.code, body) from e


def get_ref(owner: str, repo: str, branch: str, token: str) -> dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{branch}"
    return _request("GET", url, token)


def get_commit(owner: str, repo: str, sha: str, token: str) -> dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/git/commits/{sha}"
    return _request("GET", url, token)


def create_blob(owner: str, repo: str, content: str, token: str) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/git/blobs"
    # GitHub expects utf-8 content or base64
    body = {"content": content, "encoding": "utf-8"}
    r = _request("POST", url, token, body)
    return str(r["sha"])


def create_tree(
    owner: str,
    repo: str,
    base_tree: str,
    entries: list[dict[str, str]],
    token: str,
) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees"
    tree = [
        {
            "path": e["path"],
            "mode": "100644",
            "type": "blob",
            "sha": e["sha"],
        }
        for e in entries
    ]
    r = _request("POST", url, token, {"base_tree": base_tree, "tree": tree})
    return str(r["sha"])


def create_commit(
    owner: str,
    repo: str,
    message: str,
    tree_sha: str,
    parent_sha: str,
    token: str,
) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/git/commits"
    r = _request(
        "POST",
        url,
        token,
        {"message": message, "tree": tree_sha, "parents": [parent_sha]},
    )
    return str(r["sha"])


def update_ref(owner: str, repo: str, branch: str, commit_sha: str, token: str) -> dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}"
    return _request("PATCH", url, token, {"sha": commit_sha, "force": False})


class GitDataApiExecutor:
    """Real publish via Git Data API. Reads file contents from source paths dict."""

    def publish(self, plan: dict[str, Any], token: str) -> dict[str, Any]:
        if not token:
            return {"ok": False, "reason": "NO_TOKEN"}
        repo_full = str(plan.get("repository") or "")
        if "/" not in repo_full:
            return {"ok": False, "reason": "BAD_REPOSITORY"}
        owner, repo = repo_full.split("/", 1)
        branch = str(plan.get("branch") or "main")
        prefix = str(plan.get("path_prefix") or "").strip("/")
        files = list(plan.get("files") or [])
        # plan may include content_map: destination -> text
        content_map: dict[str, str] = dict(plan.get("content_map") or {})

        try:
            ref = get_ref(owner, repo, branch, token)
            commit_sha = ref["object"]["sha"]
            commit = get_commit(owner, repo, commit_sha, token)
            base_tree = commit["tree"]["sha"]

            entries = []
            for f in files:
                dest = f["destination"]
                if prefix:
                    dest = f"{prefix}/{dest}".replace("//", "/")
                content = content_map.get(f["destination"]) or content_map.get(dest)
                if content is None:
                    # source path only — executor requires content_map for real mode
                    return {
                        "ok": False,
                        "reason": "MISSING_CONTENT",
                        "destination": dest,
                        "hint": "pass content_map in plan",
                    }
                blob_sha = create_blob(owner, repo, content, token)
                entries.append({"path": dest, "sha": blob_sha})

            tree_sha = create_tree(owner, repo, base_tree, entries, token)
            new_commit = create_commit(
                owner,
                repo,
                str(plan.get("commit_message") or "wordflow publish"),
                tree_sha,
                commit_sha,
                token,
            )
            update_ref(owner, repo, branch, new_commit, token)
            return {
                "ok": True,
                "mode": "git_data_api",
                "commit_sha": new_commit,
                "tree_sha": tree_sha,
                "files": len(entries),
                "repository": repo_full,
                "branch": branch,
            }
        except GitHubApiError as e:
            return {
                "ok": False,
                "reason": "API_ERROR",
                "status": e.status,
                # body may contain secrets — truncate, never echo token
                "status_body_len": len(e.body),
            }
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "reason": "EXCEPTION", "error": type(e).__name__}
