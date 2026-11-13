# -*- coding: utf-8 -*-
"""control/threat.py — Threat Analyzer 0% LLM.
Fuente: SALIDA 4 §16 · CAPA_CONTROL_1 A3
risk_score 0-10 desde Fingerprint + risk_matrix.yaml
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

from .fingerprint import Fingerprint

_DEFAULT_MATRIX: Dict[str, Any] = {
    "data": {"public": 0, "internal": 2, "secret": 5},
    "operation": {
        "read": 1, "write": 3, "delete": 5, "install": 3,
        "mount": 3, "exec": 4, "network": 2, "unknown": 2,
    },
    "external": {"none": 0, "api": 3, "unknown": 5},
    "bands": {
        "normal": [0, 3],
        "sheriff_check": [4, 7],
        "quarantine": [8, 10],
    },
}


def load_risk_matrix(path: Optional[Path] = None) -> Dict[str, Any]:
    if path is None:
        path = Path(__file__).resolve().parents[1] / "rules" / "risk_matrix.yaml"
    if path.is_file() and yaml is not None:
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if data:
            return data
    return dict(_DEFAULT_MATRIX)


@dataclass(frozen=True)
class ThreatResult:
    risk_score: int
    band: str
    axes: Dict[str, int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_score": self.risk_score,
            "band": self.band,
            "axes": dict(self.axes),
        }


def _band_for(score: int, bands: Dict[str, Any]) -> str:
    for name, rng in bands.items():
        lo, hi = int(rng[0]), int(rng[1])
        if lo <= score <= hi:
            return name
    return "quarantine" if score >= 8 else "normal"


def analyze_threat(
    fp: Fingerprint,
    matrix: Optional[Dict[str, Any]] = None,
) -> ThreatResult:
    """Calcula risk_score 0-10. Determinista. 0% LLM."""
    m = matrix or load_risk_matrix()
    data_axis = m.get("data", {})
    op_axis = m.get("operation", {})
    ext_axis = m.get("external", {})
    bands = m.get("bands", _DEFAULT_MATRIX["bands"])

    if fp.credentials:
        d = int(data_axis.get("secret", 5))
    else:
        d = int(data_axis.get("public", 0))

    o = int(op_axis.get(fp.action, op_axis.get("unknown", 2)))
    if fp.writes and fp.action in ("read", "unknown"):
        o = max(o, int(op_axis.get("write", 3)))

    if fp.external or fp.network:
        e = int(ext_axis.get("api", 3))
        if fp.external and not fp.network:
            e = int(ext_axis.get("unknown", 5))
    else:
        e = int(ext_axis.get("none", 0))

    raw = d + o + e
    if fp.irreversible:
        raw += 2
    score = max(0, min(10, raw))
    axes = {"data": d, "operation": o, "external": e}
    return ThreatResult(risk_score=score, band=_band_for(score, bands), axes=axes)
