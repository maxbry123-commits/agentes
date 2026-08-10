# -*- coding: utf-8 -*-
"""Cursor techniques hooks — A-WF-10. Catalog loader + apply. 0% LLM."""
from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


def _catalog_path() -> Path:
    return Path(__file__).resolve().parents[1] / "store" / "cursor_techniques.yaml"


def load_techniques(path: Path | str | None = None) -> list[dict[str, Any]]:
    if yaml is None:
        raise RuntimeError("PyYAML required")
    p = Path(path) if path else _catalog_path()
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return list(data.get("techniques") or [])


def techniques_for_hook(hook: str, path: Path | str | None = None) -> list[dict[str, Any]]:
    return [t for t in load_techniques(path) if t.get("hook") == hook]


def apply_hooks(
    hook: str,
    context: dict[str, Any],
    path: Path | str | None = None,
) -> dict[str, Any]:
    applied = []
    violations = []
    for t in techniques_for_hook(hook, path):
        tid = t["id"]
        applied.append(tid)
        if tid == "CT-04" and context.get("loc") is not None:
            if int(context["loc"]) > 300:
                violations.append({"id": tid, "reason": "LOC_CAP", "loc": context["loc"]})
        if tid == "CT-09" and context.get("quality_bar") == "never_MVP":
            if not context.get("success_criteria"):
                violations.append({"id": tid, "reason": "NEVER_MVP_NO_CRITERIA"})
        if tid == "CT-10" and context.get("has_secret"):
            violations.append({"id": tid, "reason": "SECRET_IN_INPUT"})
        if tid == "CT-08" and context.get("uncertain"):
            violations.append({"id": tid, "reason": "FAIL_CLOSED"})
    return {
        "hook": hook,
        "applied": applied,
        "violations": violations,
        "ok": len(violations) == 0,
    }
