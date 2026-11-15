"""Contract Set Compiler · merge + dedup + orden · 0% LLM.

Pipeline: fingerprint → threat → base routes → modifiers → graph → reverse → set ordenado.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, List, Mapping, Optional

from .fingerprint import Fingerprint, build_fingerprint
from .graph import expand_dependencies, topological_order
from .reverse import ReverseReport, reverse_or_raise, reverse_validate
from .rules import apply_modifiers, base_contracts_for, load_dependencies
from .threat import ThreatResult, analyze_threat


@dataclass(frozen=True)
class ContractSet:
    op_type: str
    suggested_op_type: str
    contracts: tuple[str, ...]
    risk_score: int
    band: str
    fingerprint_hash: str
    set_hash: str
    elevated: bool
    reverse_ok: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _set_hash(contracts: List[str]) -> str:
    raw = json.dumps(contracts, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def compile_contract_set(
    *,
    op_type: str,
    path: str | None = None,
    payload: Mapping[str, Any] | None = None,
    flags: Mapping[str, bool] | None = None,
    strict_reverse: bool = True,
) -> ContractSet:
    """Compila el set de contratos para una operación. Determinista."""
    fp = build_fingerprint(op_type=op_type, path=path, payload=payload, flags=flags)
    threat = analyze_threat(fp)

    effective_op = threat.suggested_op_type if threat.elevated else fp.op_type
    base = base_contracts_for(effective_op)
    # también union con op original por si elevación no reemplaza todo
    base |= base_contracts_for(fp.op_type)
    with_mods = apply_modifiers(base, fp=fp, threat=threat)
    depends = load_dependencies()
    expanded = expand_dependencies(with_mods, depends)
    ordered = topological_order(expanded, depends)

    if strict_reverse:
        rev = reverse_or_raise(fp, ordered)
    else:
        rev = reverse_validate(fp, ordered)

    return ContractSet(
        op_type=fp.op_type,
        suggested_op_type=effective_op,
        contracts=tuple(ordered),
        risk_score=threat.risk_score,
        band=threat.band,
        fingerprint_hash=fp.fingerprint_hash,
        set_hash=_set_hash(ordered),
        elevated=threat.elevated,
        reverse_ok=rev.ok,
    )
