from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import os
import urllib.error
import urllib.request


@dataclass
class RepoFile:
    path: str
    sha: str
    size: int


class RepoTruthPort:
    def list_files(self, ref=None) -> list[RepoFile]:
        raise NotImplementedError

    def read_file(self, path, ref=None) -> bytes:
        raise NotImplementedError

    def head(self, ref=None) -> str:
        raise NotImplementedError

    def exists(self, path, ref=None) -> bool:
        try:
            self.read_file(path, ref)
            return True
        except Exception:
            return False

    def file_sha(self, path, ref=None) -> str | None:
        try:
            data = self.read_file(path, ref)
            return hashlib.sha1(data).hexdigest()
        except Exception:
            return None


class LocalRepoTruth(RepoTruthPort):
    def __init__(self, root):
        self.root = Path(root).resolve()

    def list_files(self, ref=None):
        result = []
        for p in self.root.rglob("*"):
            if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts:
                data = p.read_bytes()
                result.append(
                    RepoFile(
                        str(p.relative_to(self.root)),
                        hashlib.sha1(data).hexdigest(),
                        len(data),
                    )
                )
        return sorted(result, key=lambda x: x.path)

    def read_file(self, path, ref=None):
        p = (self.root / path).resolve()
        if self.root not in p.parents and p != self.root:
            raise ValueError("path escapes repository")
        return p.read_bytes()

    def head(self, ref=None):
        head = self.root / ".git" / "HEAD"
        return head.read_text(encoding="utf-8").strip() if head.exists() else "LOCAL"


class GitHubRepoTruth(RepoTruthPort):
    """Read-only GitHub Contents API. Token from env GITHUB_TOKEN only — never in body."""

    def __init__(self, owner: str, repo: str, ref: str = "main", token: str | None = None):
        self.owner = owner
        self.repo = repo
        self.ref = ref
        self.token = token if token is not None else os.environ.get("GITHUB_TOKEN", "")
        self.api = "https://api.github.com"

    def _headers(self) -> dict:
        h = {"Accept": "application/vnd.github+json", "User-Agent": "wordflow-repo-truth"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _get(self, url: str) -> dict | list:
        req = urllib.request.Request(url, headers=self._headers())
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def head(self, ref=None):
        r = ref or self.ref
        url = f"{self.api}/repos/{self.owner}/{self.repo}/commits/{r}"
        try:
            data = self._get(url)
            return str(data.get("sha", r))
        except Exception:
            return r

    def list_files(self, ref=None):
        """Recursive tree via git trees API (truncated if huge — caller should scope)."""
        r = ref or self.ref
        sha = self.head(r)
        url = f"{self.api}/repos/{self.owner}/{self.repo}/git/trees/{sha}?recursive=1"
        try:
            data = self._get(url)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"GitHub list_files failed: {e.code}") from e
        out = []
        for item in data.get("tree", []):
            if item.get("type") != "blob":
                continue
            out.append(
                RepoFile(
                    path=item["path"],
                    sha=item.get("sha", ""),
                    size=int(item.get("size") or 0),
                )
            )
        return sorted(out, key=lambda x: x.path)

    def read_file(self, path, ref=None):
        r = ref or self.ref
        url = f"{self.api}/repos/{self.owner}/{self.repo}/contents/{path}?ref={r}"
        try:
            data = self._get(url)
        except urllib.error.HTTPError as e:
            raise FileNotFoundError(path) from e
        import base64

        if isinstance(data, dict) and data.get("encoding") == "base64":
            return base64.b64decode(data["content"])
        raise RuntimeError("unexpected contents payload")


def build_repo_truth(target: str, **kwargs) -> RepoTruthPort:
    """target: local:/path or github:owner/repo[@ref]"""
    if target.startswith("local:"):
        return LocalRepoTruth(target[len("local:") :])
    if target.startswith("github:"):
        body = target[len("github:") :]
        ref = "main"
        if "@" in body:
            body, ref = body.rsplit("@", 1)
        owner, repo = body.split("/", 1)
        return GitHubRepoTruth(owner, repo, ref=ref, token=kwargs.get("token"))
    return LocalRepoTruth(target)
