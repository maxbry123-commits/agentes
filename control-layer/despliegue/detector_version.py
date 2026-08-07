"""Detector de versión semver por hash de archivos.
SOURCE: CAPA DE CONTROL 1 PASO 3
"""
from __future__ import annotations
from pathlib import Path
import hashlib


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def detect(staging: str | Path, previous: dict[str, str] | None = None) -> dict:
    stage = Path(staging)
    current: dict[str, str] = {}
    for p in stage.rglob("*"):
        if p.is_file():
            current[str(p.relative_to(stage))] = file_hash(p)

    prev = previous or {}
    added = [k for k in current if k not in prev]
    removed = [k for k in prev if k not in current]
    changed = [k for k in current if k in prev and current[k] != prev[k]]

    if removed:
        bump = "major"
    elif added:
        bump = "minor"
    elif changed:
        bump = "patch"
    else:
        bump = "none"

    return {"bump": bump, "added": added, "removed": removed, "changed": changed, "hashes": current}
