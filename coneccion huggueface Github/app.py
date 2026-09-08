"""Public Claude Chat -> Hugging Face -> GitHub backup MCP.

Authentication at the MCP layer is intentionally disabled to avoid repeated
Hugging Face OAuth prompts in Claude. The GitHub PAT remains stored only as a
Hugging Face Space secret and is never returned by any tool.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote

import httpx
from fastmcp import FastMCP

GITHUB_API = "https://api.github.com"
GITHUB_API_VERSION = "2022-11-28"
DEFAULT_OWNER = os.getenv("GITHUB_DEFAULT_OWNER", "maxbry123-commits")
STORAGE_ROOT = Path(os.getenv("HF_STORAGE_ROOT", "/data/repos"))


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _github_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_required_env('GITHUB_PERSONAL_ACCESS_TOKEN')}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
        "User-Agent": "maxbry-claude-chat-backup-mcp/2.1",
    }


def _safe_storage_path(repository: str, relative_path: str = "") -> Path:
    repo_key = repository.replace("/", "__").replace("..", "_")
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Unsafe storage path")
    target = (STORAGE_ROOT / repo_key / relative).resolve()
    root = (STORAGE_ROOT / repo_key).resolve()
    if target != root and root not in target.parents:
        raise ValueError("Storage path escapes repository namespace")
    return target


async def _github_request(
    method: str,
    path: str,
    *,
    json_body: Any | None = None,
    params: dict[str, Any] | None = None,
) -> Any:
    if not path.startswith("/"):
        path = "/" + path
    async with httpx.AsyncClient(base_url=GITHUB_API, headers=_github_headers(), timeout=60.0) as client:
        response = await client.request(method.upper(), path, json=json_body, params=params)
    if response.status_code == 204:
        return {"ok": True, "status": 204}
    try:
        payload: Any = response.json()
    except ValueError:
        payload = {"text": response.text}
    if response.is_error:
        message = payload.get("message") if isinstance(payload, dict) else str(payload)
        raise RuntimeError(f"GitHub API {response.status_code}: {message}")
    return payload


mcp = FastMCP(
    name="Maxbry GitHub Backup",
    instructions=(
        "Public MCP endpoint for Claude Chat with GitHub capability supplied by a Space secret. "
        "Use explicit owner/repository/path values, read before destructive changes, and report GitHub SHAs."
    ),
)


@mcp.tool
async def connection_status() -> dict[str, Any]:
    """Verify GitHub identity, secret presence and mounted HF storage."""
    gh_user = await _github_request("GET", "/user")
    return {
        "ok": True,
        "mcp_auth": "disabled",
        "github_login": gh_user.get("login"),
        "github_id": gh_user.get("id"),
        "default_owner": DEFAULT_OWNER,
        "secret_present": bool(os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")),
        "storage_root": str(STORAGE_ROOT),
        "storage_available": STORAGE_ROOT.parent.exists(),
    }


@mcp.tool
async def list_repositories(
    affiliation: str = "owner,collaborator,organization_member",
    visibility: str = "all",
    per_page: int = 100,
    page: int = 1,
) -> Any:
    """List repositories accessible to the dedicated GitHub PAT."""
    return await _github_request(
        "GET",
        "/user/repos",
        params={
            "affiliation": affiliation,
            "visibility": visibility,
            "per_page": min(max(per_page, 1), 100),
            "page": max(page, 1),
            "sort": "updated",
        },
    )


@mcp.tool
async def get_file(repository: str, path: str, owner: str = DEFAULT_OWNER, ref: str | None = None) -> dict[str, Any]:
    """Read a UTF-8 repository file and return its content plus blob SHA."""
    params = {"ref": ref} if ref else None
    payload = await _github_request("GET", f"/repos/{quote(owner, safe='')}/{quote(repository, safe='')}/contents/{quote(path, safe='/')}", params=params)
    if not isinstance(payload, dict) or payload.get("type") != "file":
        raise RuntimeError("Requested path is not a file")
    encoded = str(payload.get("content", "")).replace("\n", "")
    decoded = base64.b64decode(encoded).decode("utf-8") if encoded else ""
    return {"owner": owner, "repository": repository, "path": path, "ref": ref, "sha": payload.get("sha"), "content": decoded, "html_url": payload.get("html_url")}


@mcp.tool
async def create_or_update_file(repository: str, path: str, content: str, message: str, owner: str = DEFAULT_OWNER, branch: str | None = None, current_sha: str | None = None) -> Any:
    """Create or fully replace a UTF-8 file."""
    endpoint = f"/repos/{quote(owner, safe='')}/{quote(repository, safe='')}/contents/{quote(path, safe='/')}"
    if current_sha is None:
        try:
            existing = await _github_request("GET", endpoint, params={"ref": branch} if branch else None)
            if isinstance(existing, dict) and existing.get("type") == "file":
                current_sha = existing.get("sha")
        except RuntimeError as exc:
            if "GitHub API 404:" not in str(exc):
                raise
    body: dict[str, Any] = {"message": message, "content": base64.b64encode(content.encode("utf-8")).decode("ascii")}
    if branch:
        body["branch"] = branch
    if current_sha:
        body["sha"] = current_sha
    return await _github_request("PUT", endpoint, json_body=body)


@mcp.tool
async def delete_file(repository: str, path: str, message: str, owner: str = DEFAULT_OWNER, branch: str | None = None, current_sha: str | None = None) -> Any:
    """Delete a repository file."""
    endpoint = f"/repos/{quote(owner, safe='')}/{quote(repository, safe='')}/contents/{quote(path, safe='/')}"
    if current_sha is None:
        existing = await _github_request("GET", endpoint, params={"ref": branch} if branch else None)
        if not isinstance(existing, dict) or not existing.get("sha"):
            raise RuntimeError("Unable to resolve current file SHA")
        current_sha = str(existing["sha"])
    body: dict[str, Any] = {"message": message, "sha": current_sha}
    if branch:
        body["branch"] = branch
    return await _github_request("DELETE", endpoint, json_body=body)


@mcp.tool
async def create_branch(repository: str, branch: str, owner: str = DEFAULT_OWNER, from_ref: str = "main") -> Any:
    """Create a branch from an existing branch/tag/commit ref."""
    base = await _github_request("GET", f"/repos/{quote(owner, safe='')}/{quote(repository, safe='')}/git/ref/heads/{quote(from_ref, safe='/')}")
    return await _github_request("POST", f"/repos/{quote(owner, safe='')}/{quote(repository, safe='')}/git/refs", json_body={"ref": f"refs/heads/{branch}", "sha": base["object"]["sha"]})


@mcp.tool
async def delete_branch(repository: str, branch: str, owner: str = DEFAULT_OWNER) -> Any:
    """Delete a Git branch."""
    return await _github_request("DELETE", f"/repos/{quote(owner, safe='')}/{quote(repository, safe='')}/git/refs/heads/{quote(branch, safe='/')}")


@mcp.tool
async def create_issue(repository: str, title: str, body: str = "", owner: str = DEFAULT_OWNER) -> Any:
    """Create a GitHub issue."""
    return await _github_request("POST", f"/repos/{quote(owner, safe='')}/{quote(repository, safe='')}/issues", json_body={"title": title, "body": body})


@mcp.tool
async def create_pull_request(repository: str, title: str, head: str, base: str = "main", body: str = "", owner: str = DEFAULT_OWNER, draft: bool = False) -> Any:
    """Create a pull request."""
    return await _github_request("POST", f"/repos/{quote(owner, safe='')}/{quote(repository, safe='')}/pulls", json_body={"title": title, "head": head, "base": base, "body": body, "draft": draft})


@mcp.tool
async def delete_repository(repository: str, owner: str = DEFAULT_OWNER) -> Any:
    """Permanently delete a repository."""
    return await _github_request("DELETE", f"/repos/{quote(owner, safe='')}/{quote(repository, safe='')}")


@mcp.tool
async def github_api(method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"], path: str, body: dict[str, Any] | None = None, params: dict[str, Any] | None = None) -> Any:
    """Call an arbitrary api.github.com REST path with the dedicated PAT."""
    return await _github_request(method, path, json_body=body, params=params)


@mcp.tool
async def storage_write(repository: str, path: str, content: str) -> dict[str, Any]:
    """Write UTF-8 content into the mounted Hugging Face Storage Bucket namespace for a repository."""
    target = _safe_storage_path(repository, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"ok": True, "repository": repository, "path": path, "storage_path": str(target), "bytes": len(content.encode("utf-8"))}


@mcp.tool
async def storage_read(repository: str, path: str) -> dict[str, Any]:
    """Read UTF-8 content from the mounted Hugging Face Storage Bucket namespace for a repository."""
    target = _safe_storage_path(repository, path)
    return {"ok": True, "repository": repository, "path": path, "storage_path": str(target), "content": target.read_text(encoding="utf-8")}


@mcp.tool
async def storage_list(repository: str, path: str = "") -> dict[str, Any]:
    """List entries inside one repository namespace in the mounted Hugging Face Storage Bucket."""
    target = _safe_storage_path(repository, path)
    target.mkdir(parents=True, exist_ok=True)
    return {"ok": True, "repository": repository, "path": path, "storage_path": str(target), "entries": sorted(p.name for p in target.iterdir())}


if __name__ == "__main__":
    port = int(os.getenv("PORT", os.getenv("GRADIO_SERVER_PORT", "7860")))
    mcp.run(transport="http", host="0.0.0.0", port=port)
