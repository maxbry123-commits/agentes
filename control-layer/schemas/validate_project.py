"""Validador del schema project_docs — identifica B1–B8 + config.
SOURCE: schemas/project_docs.yaml
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import fnmatch


@dataclass
class ProjectValidation:
    ok: bool
    missing: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    found: list[str] = field(default_factory=list)


REQUIRED = {
    "B1": "PROJECT_MANIFEST.md",
    "B2": "state.json",
    "B8": "recovery/RECOVERY.yaml",
}
REQUIRED_GLOBS = {
    "B3": "nodes/*.yaml",
    "B4": "dag/DAG-*.yaml",
    "B5": "loops/L*.yaml",
    "B6": "council/*.yaml",
    "B7": "plan/PLAN_*.md",
}


def _glob_ok(root: Path, pattern: str) -> bool:
    return any(root.glob(pattern))


def validate_project(root: str | Path) -> ProjectValidation:
    r = Path(root)
    missing: list[str] = []
    found: list[str] = []
    warnings: list[str] = []

    for key, rel in REQUIRED.items():
        p = r / rel
        if p.exists():
            found.append(key)
        else:
            missing.append(f"{key}:{rel}")

    for key, pattern in REQUIRED_GLOBS.items():
        if _glob_ok(r, pattern):
            found.append(key)
        else:
            missing.append(f"{key}:{pattern}")

    for cfg in ("config/token_ref.yaml", "config/repo_destino.yaml", "config/backup_destino.yaml"):
        if not (r / cfg).exists():
            warnings.append(f"optional_missing:{cfg}")

    # rechazo si hay secretos en claro (heurística)
    for p in r.rglob("*"):
        if p.is_file() and p.suffix in {".yaml", ".yml", ".json", ".env", ".md"}:
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if "ghp_" in text or "github_pat_" in text:
                missing.append(f"SECRET_IN_TREE:{p.relative_to(r)}")

    return ProjectValidation(ok=len(missing) == 0, missing=missing, warnings=warnings, found=found)
