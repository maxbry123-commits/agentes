"""GitDataAPIPort — blob → tree → commit → ref.

FakePort: offline / dry-run.
RealGitDataAPIPort: GitHub Git Data API when GITHUB_DEPLOY_REAL=1 and token present.
Never force_push. expected_head mismatch → CONFLICT HOLD.
Token only from env/credential resolution — never hardcode.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class FileChange:
    path: str
    content: bytes
    mode: str = "100644"


@dataclass
class DeployResult:
    status: str  # OK | DRY_RUN | CONFLICT | ERROR | DENY
    commit_sha: str | None = None
    tree_sha: str | None = None
    message: str = ""
    detail: dict[str, Any] = field(default_factory=dict)


class GitDataAPIPort(Protocol):
    def deploy(
        self,
        owner: str,
        repo: str,
        branch: str,
        changes: list[FileChange],
        commit_message: str,
        expected_head: str | None = None,
    ) -> DeployResult: ...


class FakeGitDataAPIPort:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def deploy(
        self,
        owner: str,
        repo: str,
        branch: str,
        changes: list[FileChange],
        commit_message: str,
        expected_head: str | None = None,
    ) -> DeployResult:
        fake_sha = hashlib.sha1(
            f"{owner}/{repo}@{branch}:{commit_message}:{len(changes)}".encode()
        ).hexdigest()
        self.calls.append(
            {
                "owner": owner,
                "repo": repo,
                "branch": branch,
                "files": [c.path for c in changes],
                "message": commit_message,
                "expected_head": expected_head,
            }
        )
        return DeployResult(
            status="DRY_RUN",
            commit_sha=fake_sha,
            tree_sha=fake_sha[:40],
            message="fake deploy",
            detail={"files": len(changes)},
        )


class RealGitDataAPIPort:
    def __init__(self, token: str | None = None, api: str = "https://api.github.com"):
        self.token = token if token is not None else os.environ.get("GITHUB_TOKEN", "")
        self.api = api.rstrip("/")

    def _headers(self) -> dict:
        h = {
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "wordflow-git-data-port",
        }
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _request(self, method: str, url: str, body: dict | None = None) -> dict:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, headers=self._headers(), method=method)
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())

    def deploy(
        self,
        owner: str,
        repo: str,
        branch: str,
        changes: list[FileChange],
        commit_message: str,
        expected_head: str | None = None,
    ) -> DeployResult:
        if not self.token:
            return DeployResult(status="DENY", message="GITHUB_TOKEN empty")
        try:
            ref_url = f"{self.api}/repos/{owner}/{repo}/git/ref/heads/{branch}"
            ref = self._request("GET", ref_url)
            head = ref["object"]["sha"]
            if expected_head and expected_head != head:
                return DeployResult(
                    status="CONFLICT",
                    message="expected_head mismatch",
                    detail={"expected": expected_head, "actual": head},
                )
            blobs = []
            for ch in changes:
                b = self._request(
                    "POST",
                    f"{self.api}/repos/{owner}/{repo}/git/blobs",
                    {"content": base64.b64encode(ch.content).decode(), "encoding": "base64"},
                )
                blobs.append({"path": ch.path, "mode": ch.mode, "type": "blob", "sha": b["sha"]})
            tree = self._request(
                "POST",
                f"{self.api}/repos/{owner}/{repo}/git/trees",
                {"base_tree": head, "tree": blobs},
            )
            commit = self._request(
                "POST",
                f"{self.api}/repos/{owner}/{repo}/git/commits",
                {"message": commit_message, "tree": tree["sha"], "parents": [head]},
            )
            # no force
            self._request(
                "PATCH",
                ref_url,
                {"sha": commit["sha"], "force": False},
            )
            return DeployResult(
                status="OK",
                commit_sha=commit["sha"],
                tree_sha=tree["sha"],
                message="deployed",
            )
        except urllib.error.HTTPError as e:
            return DeployResult(
                status="ERROR",
                message=f"http_{e.code}",
                detail={"body": e.read().decode("utf-8", errors="replace")[:500]},
            )
        except Exception as e:  # noqa: BLE001
            return DeployResult(status="ERROR", message=type(e).__name__)


def build_git_data_port(dry_run: bool | None = None) -> FakeGitDataAPIPort | RealGitDataAPIPort:
    if dry_run is None:
        dry_run = os.environ.get("GITHUB_DEPLOY_REAL", "").lower() not in ("1", "true", "yes")
    if dry_run or not os.environ.get("GITHUB_TOKEN"):
        return FakeGitDataAPIPort()
    return RealGitDataAPIPort()
