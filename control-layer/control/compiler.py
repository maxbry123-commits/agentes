"""Contract Set Compiler — merge + dedup + orden.
SOURCE: SALIDA_4 · Contract Compiler 4 fases
INPUT → fingerprint → threat → rules → compiler → Sheriff
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .rules import select_contracts
from .fingerprint import Fingerprint


@dataclass(frozen=True)
class ContractPlan:
    operation: str
    fingerprint: dict[str, Any]
    threat_score: int
    threat_level: str
    contracts: tuple[str, ...]
    allowed: bool


def compile_plan(
    text: str,
    action: str = "unknown",
    data_sensitivity: str = "internal",
) -> ContractPlan:
    raw = select_contracts(text, action, data_sensitivity)
    contracts = tuple(sorted(set(raw["contracts"])))
    return ContractPlan(
        operation=raw["operation"],
        fingerprint=raw["fingerprint"],
        threat_score=raw["threat"]["score"],
        threat_level=raw["threat"]["level"],
        contracts=contracts,
        allowed=raw["allowed"],
    )
