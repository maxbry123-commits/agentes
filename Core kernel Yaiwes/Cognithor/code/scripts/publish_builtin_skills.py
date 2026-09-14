"""Publish all builtin skills to the skill-registry on GitHub.

Creates/updates skills/{name}/skill.md + manifest.json for each builtin skill,
then updates registry.json with all entries.

Usage: python scripts/publish_builtin_skills.py
Requires: GitHub credentials in git credential manager
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

REPO_OWNER = "Alex8791-cyber"
REPO_NAME = "skill-registry"
BRANCH = "main"
API_BASE = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
PROCEDURES_DIR = Path(__file__).parent.parent / "data" / "procedures"


def get_github_token() -> str:
    """Get GitHub token from git credential manager."""
    proc = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n",
        capture_output=True,
        text=True,
        timeout=10,
    )
    for line in proc.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise RuntimeError("Could not get GitHub token from credential manager")


def github_api(method: str, path: str, data: dict | None = None, token: str = "") -> dict:
    """Make GitHub API call."""
    import urllib.request

    url = f"{API_BASE}/{path}" if not path.startswith("http") else path
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    if body:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        return {"error": error_body, "status": e.code}


def put_file(path: str, content: str, message: str, token: str, sha: str = "") -> dict:
    """Create or update a file in the repo."""
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    data: dict = {
        "message": message,
        "content": encoded,
        "branch": BRANCH,
    }
    if sha:
        data["sha"] = sha
    return github_api("PUT", f"contents/{path}", data, token)


def get_file_sha(path: str, token: str) -> str:
    """Get SHA of existing file, or empty string if not found."""
    result = github_api("GET", f"contents/{path}?ref={BRANCH}", token=token)
    return result.get("sha", "")


def parse_skill_frontmatter(md_content: str) -> dict:
    """Extract YAML frontmatter from skill markdown."""
    match = re.match(r"^---\n(.*?)\n---\n", md_content, re.DOTALL)
    if not match:
        return {}
    import yaml

    return yaml.safe_load(match.group(1)) or {}


def build_manifest(name: str, frontmatter: dict, content_hash: str) -> dict:
    """Build manifest.json for a skill."""
    return {
        "name": name,
        "version": "1.0.0",
        "description": frontmatter.get("name", name).replace("-", " ").title(),
        "author_github": REPO_OWNER,
        "category": frontmatter.get("category", "productivity"),
        "tools_required": frontmatter.get("tools_required", []),
        "trigger_keywords": frontmatter.get("trigger_keywords", []),
        "priority": frontmatter.get("priority", 5),
        "content_hash": content_hash,
    }


def build_registry_entry(name: str, frontmatter: dict, content_hash: str) -> dict:
    """Build a registry.json entry for a skill."""
    return {
        "name": name,
        "version": "1.0.0",
        "description": frontmatter.get("name", name).replace("-", " ").title(),
        "author_github": REPO_OWNER,
        "category": frontmatter.get("category", "productivity"),
        "tools_required": frontmatter.get("tools_required", []),
        "content_hash": content_hash,
        "recalled": False,
    }


def main() -> None:
    token = get_github_token()
    print(f"GitHub token: {token[:8]}...")

    # Verify access
    user = github_api("GET", "https://api.github.com/user", token=token)
    print(f"Authenticated as: {user.get('login', 'UNKNOWN')}")

    # Collect all skills
    skill_files = sorted(PROCEDURES_DIR.glob("*.md"))
    print(f"\nFound {len(skill_files)} builtin skills to publish.\n")

    registry_entries = []
    errors = []

    for skill_path in skill_files:
        name = skill_path.stem
        content = skill_path.read_text(encoding="utf-8")
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        frontmatter = parse_skill_frontmatter(content)

        print(f"Publishing: {name}")
        print(f"  Category: {frontmatter.get('category', '?')}")
        print(f"  Tools: {len(frontmatter.get('tools_required', []))}")
        print(f"  Hash: {content_hash[:16]}...")

        # Upload skill.md
        skill_remote_path = f"skills/{name}/skill.md"
        existing_sha = get_file_sha(skill_remote_path, token)
        result = put_file(
            skill_remote_path,
            content,
            f"publish: {name} skill",
            token,
            sha=existing_sha,
        )
        if "error" in result:
            print(f"  ERROR uploading skill.md: {result['error'][:100]}")
            errors.append(name)
            continue
        print(f"  skill.md: {'updated' if existing_sha else 'created'}")

        # Upload manifest.json
        manifest = build_manifest(name, frontmatter, content_hash)
        manifest_content = json.dumps(manifest, indent=2, ensure_ascii=False)
        manifest_path = f"skills/{name}/manifest.json"
        manifest_sha = get_file_sha(manifest_path, token)
        result = put_file(
            manifest_path,
            manifest_content,
            f"publish: {name} manifest",
            token,
            sha=manifest_sha,
        )
        if "error" in result:
            print(f"  ERROR uploading manifest.json: {result['error'][:100]}")
            errors.append(name)
            continue
        print(f"  manifest.json: {'updated' if manifest_sha else 'created'}")

        # Add to registry
        registry_entries.append(build_registry_entry(name, frontmatter, content_hash))

        # Rate limit: 1 second between skills (GitHub API secondary rate limit)
        time.sleep(1)

    # Update registry.json
    print(f"\nUpdating registry.json with {len(registry_entries)} skills...")
    registry = {
        "version": "1.1.0",
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "skills": registry_entries,
        "recalls": [],
    }
    registry_content = json.dumps(registry, indent=2, ensure_ascii=False)
    registry_sha = get_file_sha("registry.json", token)
    result = put_file(
        "registry.json",
        registry_content,
        f"update: registry with {len(registry_entries)} skills",
        token,
        sha=registry_sha,
    )
    if "error" in result:
        print(f"ERROR updating registry.json: {result['error'][:200]}")
    else:
        print("registry.json: updated")

    # Update publishers.json
    print("\nUpdating publishers.json...")
    publishers = {
        "publishers": [
            {
                "github_username": REPO_OWNER,
                "display_name": "Cognithor Builtin",
                "verified": True,
                "trust_level": "verified",
                "skills_published": len(registry_entries),
                "reputation_score": 100.0,
            }
        ]
    }
    publishers_content = json.dumps(publishers, indent=2, ensure_ascii=False)
    publishers_sha = get_file_sha("publishers.json", token)
    result = put_file(
        "publishers.json",
        publishers_content,
        "update: publisher profile",
        token,
        sha=publishers_sha,
    )
    if "error" in result:
        print(f"ERROR updating publishers.json: {result['error'][:200]}")
    else:
        print("publishers.json: updated")

    # Summary
    print(f"\n{'=' * 50}")
    print(f"Published: {len(registry_entries)} skills")
    print(f"Errors: {len(errors)}")
    if errors:
        print(f"Failed: {', '.join(errors)}")
    print(f"Registry: https://github.com/{REPO_OWNER}/{REPO_NAME}")


if __name__ == "__main__":
    main()
