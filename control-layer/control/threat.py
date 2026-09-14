"""Threat Analyzer — risk_matrix 3 ejes → 0-10.
SOURCE: SALIDA_4_CONTRATOS · Risk Matrix
"""
from __future__ import annotations
from dataclasses import dataclass
from .fingerprint import Fingerprint

DATA = {"public": 0, "internal": 2, "secret": 5}
OP = {"read": 1, "write": 3, "delete": 5, "install": 3, "unknown": 3}
EXT = {"none": 0, "api": 3, "unknown": 5}


@dataclass(frozen=True)
class ThreatResult:
    score: int
    level: str  # normal | sheriff_check | quarantine


def analyze(fp: Fingerprint, data_sensitivity: str = "internal") -> ThreatResult:
    op = "delete" if fp.irreversible and fp.writes else ("write" if fp.writes else "read")
    if fp.action in OP:
        op = fp.action
    external = "api" if fp.network or fp.external else "none"
    if fp.credentials:
        data_sensitivity = "secret"

    score = DATA.get(data_sensitivity, 2) + OP.get(op, 3) + EXT.get(external, 0)
    score = min(score, 10)

    if score <= 3:
        level = "normal"
    elif score <= 7:
        level = "sheriff_check"
    else:
        level = "quarantine"

    return ThreatResult(score=score, level=level)
