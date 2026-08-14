# -*- coding: utf-8 -*-
"""GitHubAcquirePort — E8. Tree/blob port + Fake. 0% LLM. No live network in Fake."""
from __future__ import annotations

from typing import Any, Protocol


class GitHubAcquirePort(Protocol):
    def get_tree(
        self,
        owner: str,
        repo: str,
        ref: str,
        *,
        recursive: bool = True,
        path_prefix: str | None = None,
    ) -> dict[str, Any]:
        """Return {ok, sha, tree:[{path,type,sha,size?}], reason?}."""
        ...

    def get_blob(
        self,
        owner: str,
        repo: str,
        sha: str,
    ) -> dict[str, Any]:
        """Return {ok, sha, content, encoding, reason?}. content decoded utf-8 if text."""
        ...


class FakeGitHubAcquirePort:
    """In-memory tree/blob for offline tests."""

    def __init__(self) -> None:
        # key: (owner, repo, ref) -> list of entries
        self._trees: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
        # key: (owner, repo, blob_sha) -> content str
        self._blobs: dict[tuple[str, str, str], str] = {}

    def seed_tree(
        self,
        owner: str,
        repo: str,
        ref: str,
        entries: list[dict[str, Any]],
        *,
        tree_sha: str = "a" * 40,
    ) -> None:
        self._trees[(owner, repo, ref)] = list(entries)
        self._tree_sha: dict[tuple[str, str, str], str] = getattr(
            self, "_tree_sha", {}
        )
        self._tree_sha[(owner, repo, ref)] = tree_sha

    def seed_blob(self, owner: str, repo: str, sha: str, content: str) -> None:
        self._blobs[(owner, repo, sha)] = content

    def get_tree(
        self,
        owner: str,
        repo: str,
        ref: str,
        *,
        recursive: bool = True,
        path_prefix: str | None = None,
    ) -> dict[str, Any]:
        key = (owner, repo, ref)
        if key not in self._trees:
            return {"ok": False, "sha": None, "tree": [], "reason": "TREE_NOT_FOUND"}
        tree = list(self._trees[key])
        if path_prefix:
            tree = [e for e in tree if str(e.get("path", "")).startswith(path_prefix)]
        if not recursive:
            # only top-level (no / in path after strip)
            tree = [e for e in tree if "/" not in str(e.get("path", "")).rstrip("/")]
        sha = getattr(self, "_tree_sha", {}).get(key, "0" * 40)
        return {"ok": True, "sha": sha, "tree": tree, "reason": None}

    def get_blob(
        self,
        owner: str,
        repo: str,
        sha: str,
    ) -> dict[str, Any]:
        key = (owner, repo, sha)
        if key not in self._blobs:
            return {
                "ok": False,
                "sha": sha,
                "content": None,
                "encoding": None,
                "reason": "BLOB_NOT_FOUND",
            }
        return {
            "ok": True,
            "sha": sha,
            "content": self._blobs[key],
            "encoding": "utf-8",
            "reason": None,
        }
