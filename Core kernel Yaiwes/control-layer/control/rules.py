# -*- coding: utf-8 -*-
"""control/rules.py — Contract Rule Engine 0% LLM.
Fuente: SALIDA 4 §14.3 · CAPA_CONTROL_1 A4
when(fingerprint) → add contratos. Set puro.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

from .fingerprint import Fingerprint

_DEFAULT_ROUTING: Dict[str, List[str]] = {
    "READ_LOCAL": ["C03", "C04", "C28", "C41"],
    "WRITE_LOCAL": ["C03", "C04", "C27", "C29", "C35", "C45", "C48"],
    "NETWORK_CALL": ["C33", "C36", "C37", "C38", "C40", "C41", "C42"],
    "LLM_CALL": ["C02", "C03", "C28", "C33", "C36", "C40", "C41", "C43", "C44", "C49", "C73"],
    "MOUNT_EXTENSION": ["C51", "C52", "C53", "C54", "C55", "C82", "C83", "C84", "C85"],
}

_DEFAULT_BUNDLES: Dict[str, List[str]] = {
    "security.bundle": ["C45", "C47", "C48", "C49"],
    "runtime.bundle": ["C03", "C28", "C33", "C36"],
}


def _load_yaml(path: Path) -> Dict[str, Any]:
    if path.is_file() and yaml is not None:
        with path.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def load_routing(path: Optional[Path] = None) -> Dict[str, List[str]]:
    if path is None:
        path = Path(__file__).resolve().parents[1] / "rules" / "routing.yaml"
    data = _load_yaml(path)
    if not data:
        return dict(_DEFAULT_ROUTING)
    return {k: list(v) for k, v in data.items() if isinstance(v, list)}


def load_bundles(path: Optional[Path] = None) -> Dict[str, List[str]]:
    if path is None:
        path = Path(__file__).resolve().parents[1] / "rules" / "bundles.yaml"
    data = _load_yaml(path)
    if not data:
        return dict(_DEFAULT_BUNDLES)
    out: Dict[str, List[str]] = {}
    for name, body in data.items():
        if isinstance(body, dict) and "requires" in body:
            out[name] = list(body["requires"])
        elif isinstance(body, list):
            out[name] = list(body)
    return out or dict(_DEFAULT_BUNDLES)


def op_type_from_fingerprint(fp: Fingerprint) -> str:
    """Mapea fingerprint → tipo de routing. Determinista."""
    if fp.action == "mount":
        return "MOUNT_EXTENSION"
    if fp.action in ("delete",) or (fp.writes and fp.irreversible):
        return "WRITE_LOCAL"
    if fp.action in ("install", "write") or fp.writes:
        return "WRITE_LOCAL"
    if fp.network and not fp.writes:
        return "NETWORK_CALL"
    if fp.action in ("read",) or (not fp.writes and not fp.network):
        return "READ_LOCAL"
    if fp.action == "exec":
        return "NETWORK_CALL"
    return "READ_LOCAL"


def select_contracts(
    fp: Fingerprint,
    routing: Optional[Dict[str, List[str]]] = None,
    bundles: Optional[Dict[str, List[str]]] = None,
    extra_bundles: Optional[List[str]] = None,
) -> List[str]:
    """Reglas when→add. Mismo fp → mismo set ordenado."""
    rt = routing or load_routing()
    bd = bundles or load_bundles()
    op = op_type_from_fingerprint(fp)
    result: Set[str] = set(rt.get(op, []))

    if fp.credentials:
        result.update(bd.get("security.bundle", []))
    if fp.network or fp.external:
        result.update(bd.get("runtime.bundle", []))

    for name in extra_bundles or []:
        result.update(bd.get(name, []))

    return sorted(result)
