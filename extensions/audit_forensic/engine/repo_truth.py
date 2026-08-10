# -*- coding: utf-8 -*-
"""RepoTruthPort — A-AUD-03. Code truth via port. 0% LLM.
FakeRepoTruth for offline tests; GitHubRepoTruth for live API.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class RepoTruthPort(Protocol):
    def get_commit(self, sha: str) -> dict[str, Any] | None: ...
    def path_exists(self, ref: str, path: str) -> bool: ...
    def get_blob_sha(self, ref: str, path: str) -> str | None: ...
    def get_workflow_run(self, run_id: str) -> dict[str, Any] | None: ...
    def get_job(self, run_id: str, job_id: str | None = None) -> dict[str, Any] | None: ...


class FakeRepoTruth:
    """In-memory port for offline tests. No network."""

    def __init__(
        self,
        *,
        commits: dict[str, dict[str, Any]] | None = None,
        tree: dict[str, set[str]] | None = None,
        blobs: dict[str, dict[str, str]] | None = None,
        runs: dict[str, dict[str, Any]] | None = None,
        jobs: dict[str, list[dict[str, Any]]] | None = None,
    ):
        self.commits = commits or {}
        self.tree = tree or {}
        self.blobs = blobs or {}
        self.runs = runs or {}
        self.jobs = jobs or {}

    def get_commit(self, sha: str) -> dict[str, Any] | None:
        return self.commits.get(sha)

    def path_exists(self, ref: str, path: str) -> bool:
        paths = self.tree.get(ref) or self.tree.get("*") or set()
        return path in paths

    def get_blob_sha(self, ref: str, path: str) -> str | None:
        by_ref = self.blobs.get(ref) or self.blobs.get("*") or {}
        return by_ref.get(path)

    def get_workflow_run(self, run_id: str) -> dict[str, Any] | None:
        return self.runs.get(str(run_id))

    def get_job(self, run_id: str, job_id: str | None = None) -> dict[str, Any] | None:
        items = self.jobs.get(str(run_id)) or []
        if not items:
            return None
        if job_id is None:
            return items[0]
        for j in items:
            if str(j.get("id")) == str(job_id) or j.get("name") == job_id:
                return j
        return None


class GitHubRepoTruth:
    """Live GitHub API implementation of RepoTruthPort."""

    def __init__(
        self,
        owner: str,
        repo: str,
        *,
        token: str | None = None,
        api_base: str = "https://api.github.com",
    ):
        self.owner = owner
        self.repo = repo
        self.token = token
        self.api_base = api_base.rstrip("/")

    def _headers(self) -> dict[str, str]:
        h = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "wordflow-audit-forensic",
        }
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _get(self, path: str) -> dict[str, Any] | list[Any] | None:
        url = f"{self.api_base}{path}"
        req = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            return None

    def get_commit(self, sha: str) -> dict[str, Any] | None:
        data = self._get(f"/repos/{self.owner}/{self.repo}/commits/{sha}")
        if not isinstance(data, dict):
            return None
        stats = data.get("stats") or {}
        return {
            "sha": data.get("sha"),
            "message": (data.get("commit") or {}).get("message"),
            "stats": {
                "additions": stats.get("additions"),
                "deletions": stats.get("deletions"),
                "total": stats.get("total"),
            },
        }

    def path_exists(self, ref: str, path: str) -> bool:
        data = self._get(
            f"/repos/{self.owner}/{self.repo}/contents/{path}?ref={ref}"
        )
        return data is not None

    def get_blob_sha(self, ref: str, path: str) -> str | None:
        data = self._get(
            f"/repos/{self.owner}/{self.repo}/contents/{path}?ref={ref}"
        )
        if isinstance(data, dict):
            return data.get("sha")
        return None

    def get_workflow_run(self, run_id: str) -> dict[str, Any] | None:
        data = self._get(
            f"/repos/{self.owner}/{self.repo}/actions/runs/{run_id}"
        )
        if not isinstance(data, dict):
            return None
        return {
            "conclusion": data.get("conclusion"),
            "head_sha": data.get("head_sha"),
            "status": data.get("status"),
            "html_url": data.get("html_url"),
            "id": data.get("id"),
        }

    def get_job(self, run_id: str, job_id: str | None = None) -> dict[str, Any] | None:
        data = self._get(
            f"/repos/{self.owner}/{self.repo}/actions/runs/{run_id}/jobs"
        )
        if not isinstance(data, dict):
            return None
        jobs = data.get("jobs") or []
        if not jobs:
            return None
        if job_id is None:
            j = jobs[0]
            return {"conclusion": j.get("conclusion"), "name": j.get("name"), "id": j.get("id")}
        for j in jobs:
            if str(j.get("id")) == str(job_id) or j.get("name") == job_id:
                return {"conclusion": j.get("conclusion"), "name": j.get("name"), "id": j.get("id")}
        return None
