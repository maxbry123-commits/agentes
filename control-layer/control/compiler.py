# -*- coding: utf-8 -*-
"""control/compiler.py — Contract Compiler 0% LLM.
Fuente: SALIDA 4 §14.7 · CAPA_CONTROL_1 A6
Pipeline: normalize → fingerprint → rules → graph → reverse → plan.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from .fingerprint import Fingerprint, build_fingerprint
from .graph import build_graph
from .normalizer import normalize
from .reverse import reverse_check
from .rules import select_contracts
from .threat import ThreatResult, analyze_threat


@dataclass
class CompilePlan:
    ok: bool
    fingerprint: Fingerprint
    threat: ThreatResult
    contracts: List[str]
    conflicts: List[str] = field(default_factory=list)
    normalized: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "normalized": self.normalized,
            "fingerprint": self.fingerprint.to_dict(),
            "threat": self.threat.to_dict(),
            "contracts": list(self.contracts),
            "conflicts": list(self.conflicts),
        }


def compile_plan(
    input_data: Union[str, Dict[str, Any], None],
    extra_bundles: Optional[List[str]] = None,
) -> CompilePlan:
    """Motor completo fingerprint→plan. Determinista. 0% LLM."""
    norm = normalize(input_data)
    fp = build_fingerprint(norm if norm else input_data)
    threat = analyze_threat(fp)
    selected = select_contracts(fp, extra_bundles=extra_bundles)
    ordered = build_graph(selected)
    ok, conflicts = reverse_check(ordered)
    return CompilePlan(
        ok=ok,
        fingerprint=fp,
        threat=threat,
        contracts=ordered,
        conflicts=conflicts,
        normalized=norm,
    )
