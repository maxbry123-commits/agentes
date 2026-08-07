"""Desplegador — aplica plan.json (sin push; push es paso runtime con token_env).
SOURCE: CAPA DE CONTROL 1 · deploy_config
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
import json
import shutil


def desplegar(project_root: str | Path, plan_path: str | Path, staging: str | Path) -> dict[str, Any]:
    root = Path(project_root)
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    if plan.get("SIN_REGLA") or plan.get("BLOQUEADOS"):
        return {"ok": False, "error": "SIN_REGLA o BLOQUEADOS — abort"}

    stage = Path(staging)
    stage.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for item in plan.get("mapped", []):
        src = root / item["src"]
        if not src.exists():
            continue
        dest = stage / item["src"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        copied.append(item["src"])

    return {"ok": True, "copied": copied, "staging": str(stage)}
