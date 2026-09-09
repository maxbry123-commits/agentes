"""Contract Engine — normalizer→fingerprint→threat→rules→graph→reverse→compiler→Sheriff.
SOURCE: SALIDA_4 pipeline 4 fases + Sheriff.
"""
from __future__ import annotations
import sys
from pathlib import Path
from typing import Any

from .normalizer import normalize
from .fingerprint import build_fingerprint
from .graph import expand
from .reverse import reverse_ok
from .compiler import compile_plan, ContractPlan

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from sheriff.states import decide  # noqa: E402


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

    sheriff = decide(
        threat_level="quarantine" if not ok_rev else plan.threat_level,
        contracts_ok=plan.allowed and ok_rev,
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
            "state": sheriff.state.value,
            "allowed": sheriff.allowed,
            "reason": sheriff.reason,
        },
    }
