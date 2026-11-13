import requests
import base64
import uuid
from pathlib import Path

def get_github_contents(repo_url: str, token: str = "") -> dict:
    """Fetch repo tree + sample files from GitHub."""
    repo_url = repo_url.strip().rstrip("/")
    parts = repo_url.replace("https://github.com/", "").split("/")
    if len(parts) < 2:
        return {"error": "Invalid GitHub URL"}
    owner, repo = parts[0], parts[1]
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Get tree
    tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
    r = requests.get(tree_url, headers=headers, timeout=15)
    if r.status_code != 200:
        return {"error": f"GitHub API error: {r.status_code} — {r.json().get('message', '')}"}

    tree = r.json().get("tree", [])
    files = [f for f in tree if f["type"] == "blob" and f.get("size", 0) < 100_000]

    # Pick interesting files (limit to 15)
    priority_ext = [".py", ".js", ".ts", ".go", ".java", ".rb", ".php",
                    ".env", ".yml", ".yaml", ".json", ".sh", ".sql", ".tf"]
    priority_names = ["Dockerfile", "docker-compose.yml", ".env", "config.py",
                      "settings.py", "auth.py", "login.py", "api.py", "routes.py",
                      "database.py", "models.py", "package.json", "requirements.txt"]

    selected = []
    for f in files:
        name = Path(f["path"]).name
        ext = Path(f["path"]).suffix
        if name in priority_names or ext in priority_ext:
            selected.append(f)
        if len(selected) >= 15:
            break

    # Fetch file contents
    content_map = {}
    for f in selected[:10]:
        content_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{f['path']}"
        cr = requests.get(content_url, headers=headers, timeout=10)
        if cr.status_code == 200:
            data = cr.json()
            try:
                content = base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
                content_map[f["path"]] = content[:3000]  # cap per file
            except Exception:
                pass

    return {
        "owner": owner,
        "repo": repo,
        "file_tree": [f["path"] for f in files[:80]],
        "file_contents": content_map,
    }


def create_github_pr(owner: str, repo: str, token: str, new_files: dict, commit_msg: str, pr_title: str, pr_body: str) -> str:
    """Create a new branch, commit modified files, and open a PR via GitHub API."""
    if not token:
        return "Error: GitHub token is required to create a Pull Request."
        
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    base_url = f"https://api.github.com/repos/{owner}/{repo}"
    
    # 1. Get default branch
    r = requests.get(base_url, headers=headers, timeout=10)
    if r.status_code != 200:
        return f"Error getting repo info: {r.status_code}"
    default_branch = r.json().get("default_branch", "main")
    
    # 2. Get default branch SHA
    r = requests.get(f"{base_url}/git/ref/heads/{default_branch}", headers=headers, timeout=10)
    if r.status_code != 200:
        return f"Error getting base branch ref: {r.status_code}"
    base_sha = r.json()["object"]["sha"]
    
    # 3. Create a tree with updated files
    tree_elements = []
    for path, content in new_files.items():
        tree_elements.append({
            "path": path,
            "mode": "100644",
            "type": "blob",
            "content": content
        })
        
    r = requests.post(f"{base_url}/git/trees", headers=headers, json={
        "base_tree": base_sha,
        "tree": tree_elements
    }, timeout=15)
    if r.status_code != 201:
        return f"Error creating tree: {r.status_code} - {r.text}"
    new_tree_sha = r.json()["sha"]
    
    # 4. Create commit
    r = requests.post(f"{base_url}/git/commits", headers=headers, json={
        "message": commit_msg,
        "tree": new_tree_sha,
        "parents": [base_sha]
    }, timeout=10)
    if r.status_code != 201:
        return f"Error creating commit: {r.status_code}"
    new_commit_sha = r.json()["sha"]
    
    # 5. Create new branch
    new_branch = f"redteam-fix-{uuid.uuid4().hex[:6]}"
    r = requests.post(f"{base_url}/git/refs", headers=headers, json={
        "ref": f"refs/heads/{new_branch}",
        "sha": new_commit_sha
    }, timeout=10)
    if r.status_code != 201:
        return f"Error creating branch: {r.status_code}"
        
    # 6. Create PR
    r = requests.post(f"{base_url}/pulls", headers=headers, json={
        "title": pr_title,
        "body": pr_body,
        "head": new_branch,
        "base": default_branch
    }, timeout=10)
    if r.status_code != 201:
        return f"Error creating PR: {r.status_code} - {r.text}"
        
    return r.json().get("html_url", "Failed to retrieve PR URL")
