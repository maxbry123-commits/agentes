"""Rule Engine · when→add · set puro · 0% LLM."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping, Set

from .fingerprint import Fingerprint
from .threat import ThreatResult

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None

_RULES_DIR = Path(__file__).with_name("rules")


def _load_yaml(name: str) -> dict[str, Any]:
    path = _RULES_DIR / name
    if yaml is None or not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def base_contracts_for(op_type: str, routing: Mapping[str, Any] | None = None) -> Set[str]:
    routing = routing or _load_yaml("routing.yaml")
    routes = routing.get("routes") or {}
    op = (op_type or "READ_LOCAL").strip().upper()
    return set(routes.get(op, routes.get("READ_LOCAL", [])))


def apply_modifiers(
    contracts: Set[str],
    *,
    fp: Fingerprint,
    threat: ThreatResult,
    modifiers_doc: Mapping[str, Any] | None = None,
) -> Set[str]:
    doc = modifiers_doc or _load_yaml("modifiers.yaml")
    out = set(contracts)
    ctx = {
        "is_secret": fp.is_secret,
        "is_network": fp.is_network,
        "is_exec": fp.is_exec,
        "is_delete": fp.is_delete,
        "is_write": fp.is_write,
        "is_external": fp.is_external,
        "band": threat.band,
        "elevated": threat.elevated,
        "risk_score": threat.risk_score,
    }
    for mod in doc.get("modifiers") or []:
        when = mod.get("when") or {}
        if _match(when, ctx):
            out.update(mod.get("add") or [])
    return out


def _match(when: Mapping[str, Any], ctx: Mapping[str, Any]) -> bool:
    for k, v in when.items():
        if k == "risk_score_gte":
            if int(ctx.get("risk_score", 0)) < int(v):
                return False
        elif ctx.get(k) != v:
            return False
    return True


def load_dependencies(doc: Mapping[str, Any] | None = None) -> dict[str, list[str]]:
    doc = doc or _load_yaml("dependencies.yaml")
    raw = doc.get("depends") or {}
    return {str(k): list(v) for k, v in raw.items()}
