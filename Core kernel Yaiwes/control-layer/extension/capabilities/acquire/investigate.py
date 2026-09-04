"""INVESTIGATE · pin commit · SOURCE_STRATEGY · minimal.

Generic. No project-specific branches.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from typing import Any

from .rate_governor import RateGovernor

_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass
class InvestigateResult:
    repository: str
    tag: str | None = None
    commit: str | None = None
    strategy: str = "ARCHIVE"  # ARCHIVE|GIT_CLONE|RELEASE
    archive_url: str | None = None
    size_hint: int | None = None
    needs_token: bool = False
    dry_run: bool = False
    detail: dict[str, Any] = field(default_factory=dict)
    ok: bool = True
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _parse_repo(repo: str) -> tuple[str, str]:
    repo = repo.strip().rstrip("/")
    if repo.startswith("https://github.com/"):
        parts = repo.replace("https://github.com/", "").split("/")
        return parts[0], parts[1].replace(".git", "")
    if "/" in repo:
        a, b = repo.split("/", 1)
        return a, b.replace(".git", "")
    raise ValueError(f"bad_repo:{repo}")


def _api_get(url: str, token: str | None, gov: RateGovernor) -> tuple[int, dict[str, Any], dict[str, str]]:
    if not gov.acquire_slot():
        return 429, {"error": "rate_limited"}, {}
    try:
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "wordflow-acquire/0.1",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            headers = {k: v for k, v in resp.headers.items()}
            gov.observe_headers(headers, resp.status)
            body = json.loads(resp.read().decode("utf-8") or "{}")
            return resp.status, body, headers
    except urllib.error.HTTPError as e:
        headers = {k: v for k, v in (e.headers.items() if e.headers else [])}
        gov.observe_headers(headers, e.code)
        if e.code in (401, 403):
            return e.code, {"error": "auth", "needs_token": True}, headers
        return e.code, {"error": f"http_{e.code}"}, headers
    except Exception as e:  # noqa: BLE001
        return 0, {"error": str(e)}, {}
    finally:
        gov.release_slot()


def investigate(
    repo: str,
    *,
    tag: str | None = None,
    commit: str | None = None,
    token: str | None = None,
    dry_run: bool = False,
    governor: RateGovernor | None = None,
) -> InvestigateResult:
    gov = governor or RateGovernor()
    try:
        owner, name = _parse_repo(repo)
    except ValueError as e:
        return InvestigateResult(repository=repo, ok=False, error=str(e))

    full = f"{owner}/{name}"
    pinned = commit
    used_tag = tag

    # resolve tag → commit
    if pinned and not _COMMIT_RE.match(pinned):
        return InvestigateResult(repository=full, ok=False, error="commit_not_40_hex")

    if not pinned and tag:
        status, body, _ = _api_get(
            f"https://api.github.com/repos/{owner}/{name}/git/ref/tags/{tag}",
            token, gov,
        )
        if status in (401, 403):
            return InvestigateResult(repository=full, tag=tag, needs_token=True, ok=False, error="needs_token")
        if status == 200:
            obj = body.get("object") or {}
            pinned = obj.get("sha")
            # annotated tag may need another call — keep sha if commit
            if obj.get("type") == "tag":
                st2, body2, _ = _api_get(obj.get("url") or "", token, gov)
                if st2 == 200:
                    pinned = (body2.get("object") or {}).get("sha") or pinned
        used_tag = tag

    if not pinned:
        # latest release tag optional — still require explicit pin preference
        status, body, _ = _api_get(
            f"https://api.github.com/repos/{owner}/{name}", token, gov,
        )
        if status in (401, 403):
            return InvestigateResult(repository=full, needs_token=True, ok=False, error="needs_token")
        if status != 200:
            return InvestigateResult(repository=full, ok=False, error=f"repo_lookup_{status}")
        # do not pin floating default branch as final without tag/commit
        return InvestigateResult(
            repository=full,
            ok=False,
            error="pin_required_tag_or_commit",
            detail={"default_branch": body.get("default_branch"), "size_kb": body.get("size")},
        )

    archive_url = f"https://github.com/{owner}/{name}/archive/{pinned}.tar.gz"
    strategy = "ARCHIVE"
    # crude size from repo metadata if available
    st, meta, _ = _api_get(f"https://api.github.com/repos/{owner}/{name}", token, gov)
    size_hint = None
    if st == 200:
        size_hint = int(meta.get("size") or 0) * 1024  # API size is KB
        if size_hint and size_hint > 500_000_000:
            strategy = "GIT_CLONE"

    return InvestigateResult(
        repository=full,
        tag=used_tag,
        commit=pinned,
        strategy=strategy,
        archive_url=archive_url,
        size_hint=size_hint,
        dry_run=dry_run,
        detail={"owner": owner, "name": name, "rate": gov.to_dict()},
        ok=True,
    )
