"""Contract Engine — orquesta normalizer→fingerprint→threat→rules→graph→reverse→compiler.
SOURCE: SALIDA_4 pipeline 4 fases + Sheriff.
"""
from __future__ import annotations
from typing import Any
from .normalizer import normalize
from .fingerprint import build_fingerprint
from .graph import expand
from .reverse import reverse_ok
from .compiler import compile_plan, ContractPlan

try:
    from sheriff.states import decide
except ImportError:  # ejecución desde control-layer/
    from control_layer_sheriff_fallback import decide  # type: ignore
    # fallback inline
    def decide(**kwargs):  # type: ignore
        from dataclasses import dataclass
        from enum import Enum

        class S(str, Enum):
            GREEN, YELLOW, ORANGE, RED, BLACK = "GREEN", "YELLOW", "ORANGE", "RED", "BLACK"

        @dataclass(frozen=True)
        class D:
            state: S
            allowed: bool
            reason: str

        if kwargs.get("permanent_block"):
            return D(S.BLACK, False, "bloqueado permanente")
        if kwargs.get("threat_level") == "quarantine" or not kwargs.get("contracts_ok", True) or not kwargs.get("enchufe_ok", True):
            return D(S.RED, False, "quarantine o contrato/enchufe fallido")
        if not kwargs.get("evidence_ok", True):
            return D(S.ORANGE, False, "shadow: falta evidencia")
        if kwargs.get("threat_level") == "sheriff_check":
            return D(S.YELLOW, True, "aprobado con revisión")
        return D(S.GREEN, True, "aprobado")


def run_engine(
    raw: dict[str, Any] | str,
    evidence_ok: bool = True,
    enchufe_ok: bool = True,
) -> dict[str, Any]:
    data = normalize(raw)
    plan: ContractPlan = compile_plan(
        data["text"], data["action"], data["data_sensitivity"]
    )
    contracts = expand(list(plan.contracts))
    fp = build_fingerprint(data["text"], data["action"])
    ok_rev, rev_msg = reverse_ok(contracts, fp)
    if not ok_rev:
        sheriff = decide(
            threat_level="quarantine",
            contracts_ok=False,
            enchufe_ok=enchufe_ok,
            evidence_ok=evidence_ok,
        )
    else:
        sheriff = decide(
            threat_level=plan.threat_level,
            contracts_ok=plan.allowed,
            enchufe_ok=enchufe_ok,
            evidence_ok=evidence_ok,
        )

    return {
        "plan": {
            "operation": plan.operation,
            "contracts": contracts,
            "threat_score": plan.threat_score,
            "threat_level": plan.threat_level,
            "allowed": plan.allowed and ok_rev and sheriff.allowed,
        },
        "reverse": {"ok": ok_rev, "msg": rev_msg},
        "sheriff": {
            "state": getattr(sheriff.state, "value", str(sheriff.state)),
            "allowed": sheriff.allowed,
            "reason": sheriff.reason,
        },
    }
