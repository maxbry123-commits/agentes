# -*- coding: utf-8 -*-
"""Requirement catalog loader — A-AUD-03b. 0% LLM."""
from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

CHECK_TYPES = frozenset(
    {"path_exists", "blob_keyword", "yaml_field", "ci_success", "custom"}
)

REASON = {
    "SEED_MISSING": "SEED_MISSING",
    "YAML_REQUIRED": "YAML_REQUIRED",
    "INVALID_REQUIREMENT": "INVALID_REQUIREMENT",
}


class RequirementError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def _default_seed() -> Path:
    return Path(__file__).resolve().parents[1] / "requirements" / "phase_seed.yaml"


def normalize_requirement(raw: dict[str, Any]) -> dict[str, Any]:
    rid = raw.get("id")
    if not rid:
        raise RequirementError(REASON["INVALID_REQUIREMENT"], "missing id")
    check_type = raw.get("check_type") or "path_exists"
    if check_type not in CHECK_TYPES:
        raise RequirementError(
            REASON["INVALID_REQUIREMENT"], f"check_type={check_type}"
        )
    return {
        "id": str(rid),
        "doc_id": str(raw.get("doc_id") or ""),
        "section": str(raw.get("section") or ""),
        "check_type": check_type,
        "params": dict(raw.get("params") or {}),
        "critical": bool(raw.get("critical", False)),
        "phase": str(raw.get("phase") or ""),
    }


def load_requirements(
    seed_path: Path | str | None = None,
    *,
    phase: str | None = None,
) -> list[dict[str, Any]]:
    if yaml is None:
        raise RequirementError(REASON["YAML_REQUIRED"], "PyYAML not installed")
    path = Path(seed_path) if seed_path else _default_seed()
    if not path.is_file():
        raise RequirementError(REASON["SEED_MISSING"], str(path))
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw_list = data.get("requirements") or []
    out: list[dict[str, Any]] = []
    for raw in raw_list:
        req = normalize_requirement(raw)
        if phase and req["phase"] != phase:
            continue
        out.append(req)
    return out


def by_id(reqs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {r["id"]: r for r in reqs}


def critical_only(reqs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in reqs if r.get("critical")]
