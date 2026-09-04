# -*- coding: utf-8 -*-
"""License gate — A-SE-03. PASS|DIRECTOR|STOP. 0% LLM."""
from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


def _licenses_path() -> Path:
    return Path(__file__).resolve().parents[1] / "store" / "licenses.yaml"


def load_licenses(path: Path | str | None = None) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML required")
    p = Path(path) if path else _licenses_path()
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return {
        "licenses": dict(data.get("licenses") or {}),
        "default": data.get("default") or "DIRECTOR",
    }


def check_license(
    license_id: str | None,
    path: Path | str | None = None,
) -> dict[str, Any]:
    cfg = load_licenses(path)
    lid = (license_id or "UNKNOWN").strip()
    entry = cfg["licenses"].get(lid)
    if entry is None:
        verdict = cfg["default"]
        known = False
    else:
        verdict = entry.get("verdict") or cfg["default"]
        known = True
    return {
        "license": lid,
        "verdict": verdict,
        "known": known,
        "allowed": verdict == "PASS",
        "needs_director": verdict == "DIRECTOR",
        "blocked": verdict == "STOP",
    }
