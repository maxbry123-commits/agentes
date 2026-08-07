"""Subir a GitHub — usa token SOLO desde env (nombre en token_ref del proyecto).
SOURCE: acuerdo token por proyecto · nunca valor en repo.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
import os


def _load_yaml(path: Path) -> dict:
    import yaml
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def subir(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root)
    token_ref = _load_yaml(root / "config" / "token_ref.yaml")
    repo_cfg = _load_yaml(root / "config" / "repo_destino.yaml")

    env_name = token_ref.get("token_env", "GITHUB_TOKEN")
    token = os.environ.get(env_name)
    if not token:
        return {"ok": False, "error": f"MISSING_TOKEN env={env_name}"}

    owner = repo_cfg.get("owner")
    repo = repo_cfg.get("repo")
    branch = repo_cfg.get("branch", "main")
    if not owner or not repo:
        return {"ok": False, "error": "MISSING_CONFIG repo_destino"}

    # Runtime real: gh / git push con token. Aquí solo valida precondiciones.
    return {
        "ok": True,
        "ready": True,
        "owner": owner,
        "repo": repo,
        "branch": branch,
        "token_env": env_name,
        "note": "precheck passed; execute git/gh in runtime with env token",
    }
