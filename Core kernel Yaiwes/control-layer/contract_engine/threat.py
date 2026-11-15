"""Threat Analyzer · risk_matrix FIJA · 0% LLM.

Una operación puede parecer WRITE_LOCAL pero contener credential/network/exec
y subir de banda (caso que motivó las 4 fases del Router).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .fingerprint import Fingerprint

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None  # fallback dict embebido

_DEFAULT_MATRIX: dict[str, Any] = {
    "data": {"public": 0, "internal": 2, "secret": 5},
    "operation": {"read": 1, "write": 3, "delete": 5, "exec": 4, "network": 3},
    "external": {"none": 0, "api": 3, "unknown": 5},
    "bands": {"normal": [0, 3], "sheriff_check": [4, 7], "quarantine": [8, 10]},
}


@dataclass(frozen=True)
class ThreatResult:
    risk_score: int
    band: str  # normal | sheriff_check | quarantine
    data_level: str
    operation_level: str
    external_level: str
    elevated: bool
    suggested_op_type: str  # puede re-rutar (ej. WRITE_LOCAL → CREDENTIAL_ACCESS)
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["reasons"] = list(self.reasons)
        return d


def _load_matrix(path: Path | None = None) -> dict[str, Any]:
    if path is None:
        path = Path(__file__).with_name("risk_matrix.yaml")
    if yaml is not None and path.is_file():
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return {**_DEFAULT_MATRIX, **{k: data.get(k, _DEFAULT_MATRIX[k]) for k in _DEFAULT_MATRIX}}
    return dict(_DEFAULT_MATRIX)


def _band_for(score: int, bands: dict[str, list[int]]) -> str:
    if score <= bands["normal"][1]:
        return "normal"
    if score <= bands["sheriff_check"][1]:
        return "sheriff_check"
    return "quarantine"


def analyze_threat(fp: Fingerprint, matrix: dict[str, Any] | None = None) -> ThreatResult:
    """Calcula risk_score y posible re-ruta de op_type."""
    m = matrix or _load_matrix()
    reasons: list[str] = []

    # data level
    if fp.is_secret:
        data_level = "secret"
        reasons.append("secret_detected")
    else:
        data_level = "public"

    # operation level
    if fp.is_delete:
        operation_level = "delete"
    elif fp.is_exec:
        operation_level = "exec"
        reasons.append("exec_detected")
    elif fp.is_write:
        operation_level = "write"
    elif fp.is_network:
        operation_level = "network"
    else:
        operation_level = "read"

    # external level
    if fp.is_external or fp.is_network:
        external_level = "api" if fp.is_network else "unknown"
        reasons.append("external_or_network")
    else:
        external_level = "none"

    score = (
        int(m["data"][data_level])
        + int(m["operation"][operation_level])
        + int(m["external"][external_level])
    )
    # clamp 0-10
    score = max(0, min(10, score))
    band = _band_for(score, m["bands"])

    elevated = False
    suggested = fp.op_type

    # Caso motivador: WRITE + secret → CREDENTIAL_ACCESS
    if fp.is_write and fp.is_secret:
        elevated = True
        suggested = "CREDENTIAL_ACCESS"
        reasons.append("elevate_write_with_secret_to_CREDENTIAL_ACCESS")
    elif fp.is_exec and fp.is_network:
        elevated = True
        suggested = "EXEC_NETWORK"
        reasons.append("elevate_exec_network")
    elif band == "quarantine" and not fp.op_type.startswith("CREDENTIAL"):
        elevated = True
        reasons.append("quarantine_band")

    return ThreatResult(
        risk_score=score,
        band=band,
        data_level=data_level,
        operation_level=operation_level,
        external_level=external_level,
        elevated=elevated,
        suggested_op_type=suggested,
        reasons=tuple(reasons),
    )
