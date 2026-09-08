"""Claude Chat -> Hugging Face -> GitHub backup MCP.

This server is intentionally independent from GitHub's hosted MCP endpoint.
It talks to the GitHub REST API with a dedicated PAT stored only as a
Hugging Face Space secret, while Claude authenticates to this MCP through
Hugging Face OAuth.
"""

from __future__ import annotations

import base64
import hashlib
import os
from typing import Any, Literal
from urllib.parse import quote

import httpx
from cryptography.fernet import Fernet
from fastmcp import FastMCP
from fastmcp.server.auth.providers.huggingface import HuggingFaceProvider
from fastmcp.server.dependencies import get_access_token
from key_value.aio.stores.filetree import FileTreeStore
from key_value.aio.wrappers.encryption import FernetEncryptionWrapper

GITHUB_API = "https://api.github.com"
GITHUB_API_VERSION = "2022-11-28"
DEFAULT_OWNER = os.getenv("GITHUB_DEFAULT_OWNER", "maxbry123-commits")
ALLOWED_HF_USERS = {
    item.strip()
    for item in os.getenv("MCP_ALLOWED_HF_USERS", "COMAND-CENTER-1").split(",")
    if item.strip()
}


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _public_base_url() -> str:
    explicit = os.getenv("MCP_PUBLIC_BASE_URL", "").strip().rstrip("/")
    if explicit:
        return explicit
    host = os.getenv("SPACE_HOST", "").strip()
    if not host:
        raise RuntimeError("SPACE_HOST is missing; set MCP_PUBLIC_BASE_URL when running outside Hugging Face Spaces")
    return f"https://{host}"


def _require_authorized_hf_user() -> str:
    token = get_access_token()
    if token is None:
        raise PermissionError("Authentication required")
    username = str(token.claims.get("preferred_username") or "")
    if username not in ALLOWED_HF_USERS:
        raise PermissionError(f"Hugging Face user '{username}' is not allowed")
    return username


def _github_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_required_env('GITHUB_PERSONAL_ACCESS_TOKEN')}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
        "User-Agent": "maxbry-claude-chat-backup-mcp/1.0",
    }


async def _github_request(
    method: str,
    path: str,
    *,
    json_body: Any | None = None,
    params: dict[str, Any] | None = None,
) -> Any:
    _require_authorized_hf_user()
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


# Hugging Face automatically provisions these OAuth credentials when the
# Space README contains `hf_oauth: true`.
# Persist FastMCP OAuth registrations/tokens on the mounted HF bucket (/data)
# so a 5-minute Space sleep/wake does not erase Claude's auth state.
_oauth_secret = _required_env("OAUTH_CLIENT_SECRET")
_storage_key = base64.urlsafe_b64encode(hashlib.sha256(_oauth_secret.encode("utf-8")).digest())
_oauth_storage = FernetEncryptionWrapper(
    key_value=FileTreeStore(directory="/data/fastmcp-oauth"),
    fernet=Fernet(_storage_key),
)

auth = HuggingFaceProvider(
    client_id=_required_env("OAUTH_CLIENT_ID"),
    client_secret=_oauth_secret,
    base_url=_public_base_url(),
    required_scopes=["openid", "profile"],
    valid_scopes=["openid", "profile"],
    fastmcp_access_token_expiry_seconds=60 * 60 * 24 * 30,
    jwt_signing_key=_oauth_secret,
    client_storage=_oauth_storage,
)

mcp = FastMCP(
    name="Maxbry GitHub Backup",
    instructions=(
        "Backup GitHub MCP for Claude Chat. It has intentionally broad GitHub write capability. "
        "Use explicit owner/repository/path values, read before destructive changes, and report GitHub SHAs."
    ),
    auth=auth,
)


@mcp.tool
async def connection_status() -> dict[str, Any]:
    """Verify the authenticated HF caller and GitHub identity without exposing secrets."""
    hf_user = _require_authorized_hf_user()
    gh_user = await _github_request("GET", "/user")
    return {
        "ok": True,
        "hf_user": hf_user,
        "github_login": gh_user.get("login"),
        "github_id": gh_user.get("id"),
        "default_owner": DEFAULT_OWNER,
        "secret_present": bool(os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")),
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
async def get_file(
    repository: str,
    path: str,
    owner: str = DEFAULT_OWNER,
    ref: str | None = None,
) -> dict[str, Any]:
    """Read a UTF-8 repository file and return its content plus blob SHA."""
    params = {"ref": ref} if ref else None
    payload = await _github_request(
        "GET",
        f"/repos/{quote(owner, safe='')}/{quote(repository, safe='')}/contents/{quote(path, safe='/')}",
        params=params,
    )
    if not isinstance(payload, dict) or payload.get("type") != "file":
        raise RuntimeError("Requested path is not a file")
    encoded = str(payload.get("content", "")).replace("\n", "")
    decoded = base64.b64decode(encoded).decode("utf-8") if encoded else ""
    return {
        "owner": owner,
        "repository": repository,
        "path": path,
        "ref": ref,
        "sha": payload.get("sha"),
        "content": decoded,
        "html_url": payload.get("html_url"),
    }


@mcp.tool
async def create_or_update_file(
    repository: str,
    path: str,
    content: str,
    message: str,
    owner: str = DEFAULT_OWNER,
    branch: str | None = None,
    current_sha: str | None = None,
) -> Any:
    """Create or fully replace a UTF-8 file. If current_sha is omitted, detect an existing file automatically."""
    endpoint = f"/repos/{quote(owner, safe='')}/{quote(repository, safe='')}/contents/{quote(path, safe='/')}"
    if current_sha is None:
        try:
            existing = await _github_request("GET", endpoint, params={"ref": branch} if branch else None)
            if isinstance(existing, dict) and existing.get("type") == "file":
                current_sha = existing.get("sha")
        except RuntimeError as exc:
            if "GitHub API 404:" not in str(exc):
                raise
    body: dict[str, Any] = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
    }
    if branch:
        body["branch"] = branch
    if current_sha:
        body["sha"] = current_sha
    return await _github_request("PUT", endpoint, json_body=body)


@mcp.tool
async def delete_file(
    repository: str,
    path: str,
    message: str,
    owner: str = DEFAULT_OWNER,
    branch: str | None = None,
    current_sha: str | None = None,
) -> Any:
    """Delete a repository file. The current blob SHA is detected when omitted."""
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
async def create_branch(
    repository: str,
    branch: str,
    owner: str = DEFAULT_OWNER,
    from_ref: str = "main",
) -> Any:
    """Create a branch from an existing branch/tag/commit ref."""
    base = await _github_request(
        "GET",
        f"/repos/{quote(owner, safe='')}/{quote(repository, safe='')}/git/ref/heads/{quote(from_ref, safe='/')}",
    )
    sha = base["object"]["sha"]
    return await _github_request(
        "POST",
        f"/repos/{quote(owner, safe='')}/{quote(repository, safe='')}/git/refs",
        json_body={"ref": f"refs/heads/{branch}", "sha": sha},
    )


@mcp.tool
async def delete_branch(
    repository: str,
    branch: str,
    owner: str = DEFAULT_OWNER,
) -> Any:
    """Delete a Git branch."""
    return await _github_request(
        "DELETE",
        f"/repos/{quote(owner, safe='')}/{quote(repository, safe='')}/git/refs/heads/{quote(branch, safe='/')}",
    )


@mcp.tool
async def create_issue(
    repository: str,
    title: str,
    body: str = "",
    owner: str = DEFAULT_OWNER,
) -> Any:
    """Create a GitHub issue."""
    return await _github_request(
        "POST",
        f"/repos/{quote(owner, safe='')}/{quote(repository, safe='')}/issues",
        json_body={"title": title, "body": body},
    )


@mcp.tool
async def create_pull_request(
    repository: str,
    title: str,
    head: str,
    base: str = "main",
    body: str = "",
    owner: str = DEFAULT_OWNER,
    draft: bool = False,
) -> Any:
    """Create a pull request."""
    return await _github_request(
        "POST",
        f"/repos/{quote(owner, safe='')}/{quote(repository, safe='')}/pulls",
        json_body={"title": title, "head": head, "base": base, "body": body, "draft": draft},
    )


@mcp.tool
async def delete_repository(repository: str, owner: str = DEFAULT_OWNER) -> Any:
    """Permanently delete a repository. Requires Administration: write on the dedicated PAT."""
    return await _github_request(
        "DELETE",
        f"/repos/{quote(owner, safe='')}/{quote(repository, safe='')}",
    )


@mcp.tool
async def github_api(
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"],
    path: str,
    body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> Any:
    """Call an arbitrary api.github.com REST path with the dedicated PAT. This is the full-capability fallback tool."""
    return await _github_request(method, path, json_body=body, params=params)


if __name__ == "__main__":
    port = int(os.getenv("PORT", os.getenv("GRADIO_SERVER_PORT", "7860")))
    mcp.run(transport="http", host="0.0.0.0", port=port)
