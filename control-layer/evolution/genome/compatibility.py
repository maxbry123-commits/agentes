"""Compatibility Genome · PROMOTE|HOLD|REJECT."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any

@dataclass
class GenomeReport:
    decision: str
    score: float
    checks: dict = field(default_factory=dict)
    deltas: dict = field(default_factory=dict)
    reasons: list = field(default_factory=list)
    def to_dict(self): return asdict(self)

class CompatibilityGenome:
    def evaluate(self, before=None, after=None, simulation=None, license_verdict="PASS", preserved_cognitive=None, subordinated_control=None):
        before, after, simulation = before or {}, after or {}, simulation or {}
        checks, reasons, deltas = {}, [], {}
        checks["license_ok"] = license_verdict in ("PASS", "DIRECTOR")
        if not checks["license_ok"]: reasons.append("license_block")
        checks["simulation_ok"] = bool(simulation.get("ok", False))
        if not checks["simulation_ok"]: reasons.append("simulation_failed")
        before_fp = before.get("fingerprint") or {}
        after_fp = after.get("fingerprint") or after.get("evo_ir", {}).get("fingerprint") or {}
        if before_fp.get("has_code_gen"):
            checks["code_gen_retained"] = bool(after_fp.get("has_code_gen") or preserved_cognitive)
            if not checks["code_gen_retained"]: reasons.append("lost_code_gen")
        else:
            checks["code_gen_retained"] = True
        if after_fp.get("has_agent_loop") or subordinated_control:
            checks["control_subordinated"] = bool(subordinated_control)
            if not checks["control_subordinated"]: reasons.append("control_not_subordinated")
        else:
            checks["control_subordinated"] = True
        caps_after = set(after.get("registered") or after.get("capabilities") or [])
        deltas["caps_delta"] = float(len(caps_after))
        checks["caps_non_empty"] = len(caps_after) > 0
        if not checks["caps_non_empty"]: reasons.append("no_capabilities")
        score = sum(1 for v in checks.values() if v) / max(len(checks), 1)
        if not checks.get("license_ok") or not checks.get("simulation_ok"):
            decision = "REJECT"
        elif reasons:
            decision = "HOLD"
        elif score >= 0.85:
            decision = "PROMOTE"
        else:
            decision = "HOLD"; reasons.append(f"score:{score:.2f}")
        return GenomeReport(decision, score, checks, deltas, reasons)
