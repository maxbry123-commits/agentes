# -*- coding: utf-8 -*-
"""Goals IN extractor — A-WF-02. Deterministic from InputBlock. 0% LLM."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

PATH_RE = re.compile(
    r"(?:[\w.-]+/)+[\w.-]+\.(?:py|yaml|yml|json|md|toml)",
    re.IGNORECASE,
)
PHASE_RE = re.compile(
    r"\b(control-layer|audit|source-evo|wordflow|fase\s*[0-4]|wave\s*\d+)\b",
    re.IGNORECASE,
)
LOC_RE = re.compile(r"\b(\d{2,4})\s*LOC\b", re.IGNORECASE)


def _default_catalog() -> Path:
    return Path(__file__).resolve().parents[1] / "store" / "goals_catalog.yaml"


def load_goals_catalog(path: Path | str | None = None) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML required")
    p = Path(path) if path else _default_catalog()
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return {
        "version": data.get("version", "1.0"),
        "goals_in": list(data.get("goals_in") or []),
        "goals_out": list(data.get("goals_out") or []),
    }


def extract_goals_in(block: dict[str, Any]) -> dict[str, Any]:
    text = block.get("raw_text") or ""
    flags = block.get("flags") or {}
    constraints = block.get("constraints") or {}

    paths = PATH_RE.findall(text)
    phase_m = PHASE_RE.search(text)
    loc_m = LOC_RE.search(text)

    resolved = {
        "GIN-01": {"name": "extract_objective", "value": text[:200]},
        "GIN-02": {
            "name": "extract_constraints",
            "value": constraints or {"raw_hints": loc_m.group(0) if loc_m else None},
        },
        "GIN-03": {"name": "extract_quality_bar", "value": block.get("quality_bar")},
        "GIN-04": {
            "name": "extract_doc_refs",
            "value": list(block.get("doc_refs") or []),
        },
        "GIN-05": {"name": "extract_priority", "value": block.get("priority")},
        "GIN-06": {
            "name": "detect_repair",
            "value": {
                "is_repair": bool(flags.get("is_repair")),
                "parent_block_id": block.get("parent_block_id"),
            },
        },
        "GIN-07": {
            "name": "list_capabilities_needed",
            "value": list(block.get("goals_hint") or []),
        },
        "GIN-08": {"name": "list_files_hint", "value": paths},
        "GIN-09": {
            "name": "detect_phase",
            "value": phase_m.group(0).lower() if phase_m else None,
        },
        "GIN-10": {
            "name": "extract_success_criteria",
            "value": constraints.get("success_criteria"),
        },
        "GIN-11": {
            "name": "extract_tokens_budget",
            "value": {
                "loc_limit": int(loc_m.group(1)) if loc_m else constraints.get("loc_limit"),
                "tokens": constraints.get("tokens"),
            },
        },
        "GIN-12": {
            "name": "extract_agent_hint",
            "value": (block.get("meta") or {}).get("agent_hint"),
        },
    }

    covered = [gid for gid, g in resolved.items() if g["value"] not in (None, [], {}, "")]
    return {
        "resolved": resolved,
        "covered_ids": covered,
        "covered_count": len(covered),
        "total_in": 12,
        "never_mvp": bool(flags.get("never_mvp")),
        "block_id": block.get("block_id"),
        "block_hash": block.get("block_hash"),
    }


def empty_goals_out() -> dict[str, Any]:
    catalog = load_goals_catalog()
    return {
        g["id"]: {"name": g["name"], "value": None, "status": "PENDING"}
        for g in catalog["goals_out"]
    }
