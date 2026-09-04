"""HuggingFace destination port. Dry-run unless HF_DEPLOY_REAL=1."""
from __future__ import annotations

import hashlib
import os
from typing import Any


class HfPort:
    def deploy(
        self,
        owner: str,
        repo: str,
        branch: str,
        files: list[dict[str, Any]],
        commit_message: str,
        token: str,
    ) -> dict[str, Any]:
        raise NotImplementedError


class FakeHfPort(HfPort):
    def deploy(
        self,
        owner: str,
        repo: str,
        branch: str,
        files: list[dict[str, Any]],
        commit_message: str,
        token: str,
    ) -> dict[str, Any]:
        if not token:
            return {"ok": False, "status": "DENY", "reason": "NO_TOKEN"}
        digest = hashlib.sha1(f"{owner}/{repo}:{commit_message}:{len(files)}".encode()).hexdigest()
        return {
            "ok": True,
            "status": "DRY_RUN",
            "published": False,
            "commit_sha": digest,
            "repository": f"{owner}/{repo}",
            "branch": branch,
            "files": [f.get("path") for f in files],
            "provider": "huggingface",
        }


class RealHfPort(HfPort):
    def deploy(
        self,
        owner: str,
        repo: str,
        branch: str,
        files: list[dict[str, Any]],
        commit_message: str,
        token: str,
    ) -> dict[str, Any]:
        if not token:
            return {"ok": False, "status": "DENY", "reason": "NO_TOKEN"}
        try:
            from huggingface_hub import HfApi  # type: ignore
        except ImportError:
            return {"ok": False, "status": "ERROR", "reason": "HF_HUB_MISSING"}
        api = HfApi(token=token)
        repo_id = f"{owner}/{repo}"
        uploaded = []
        for f in files:
            path = str(f.get("path") or "")
            content = f.get("content") or ""
            api.upload_file(
                path_or_fileobj=content.encode("utf-8") if isinstance(content, str) else content,
                path_in_repo=path,
                repo_id=repo_id,
                repo_type=str(f.get("repo_type") or "model"),
                commit_message=commit_message,
            )
            uploaded.append(path)
        return {
            "ok": True,
            "status": "OK",
            "published": True,
            "repository": repo_id,
            "branch": branch,
            "files": uploaded,
            "provider": "huggingface",
        }


def build_hf_port(dry_run: bool | None = None) -> HfPort:
    if dry_run is None:
        dry_run = os.environ.get("HF_DEPLOY_REAL", "").lower() not in ("1", "true", "yes")
    if dry_run:
        return FakeHfPort()
    return RealHfPort()
