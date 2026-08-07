"""Bootstrap · enganche único del núcleo dual.

turn/op → Sentinela → Sheriff → (block | durable checkpoint + execute)
Usable desde WordflowApp y PluginAdapter (misma función).
"""
from __future__ import annotations

import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from contract_engine.sentinela_router import SentinelaDecision, route
from format.output_chef import format_output
from runtime.durable import DurableRuntime
from sheriff.estados import SheriffState, Verdict
from sheriff.gate import run_sheriff
from sheriff.shadow import ShadowLedger


@dataclass
class PipelineResult:
    ok: bool
    blocked: bool
    mission_id: str | None
    decision: dict[str, Any]
    verdict: dict[str, Any]
    output: dict[str, Any]
    shadow_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_control_pipeline(
    *,
    op_type: str,
    payload: Mapping[str, Any] | None = None,
    path: str | None = None,
    mount_mode: str = "dual",
    mission_id: str | None = None,
    goal: str | None = None,
    runtime: DurableRuntime | None = None,
    ledger: ShadowLedger | None = None,
    shadow_candidate: bool = False,
    strict_reverse: bool = False,
) -> PipelineResult:
    """Único enganche de control.

    1. route (Sentinela)
    2. sheriff gate
    3. si block → output BLOCKED + checkpoint opcional
    4. si ok → checkpoint durable + output RUNNING/COMPLETED shell
    """
    decision: SentinelaDecision = route(
        op_type=op_type,
        payload=payload,
        path=path,
        mount_mode=mount_mode,
        strict_reverse=strict_reverse,
    )
    verdict, shadow_rec = run_sheriff(
        decision.to_dict(),
        ledger=ledger,
        shadow_candidate=shadow_candidate or ("C55" in decision.active_contracts),
    )

    mid = mission_id
    if runtime is not None and mid is None and goal:
        st = runtime.create_mission(goal)
        mid = st.mission_id

    if runtime is not None and mid:
        runtime.checkpoint(
            mid,
            phase="blocked" if not verdict.allow_execute else "ejecutar",
            cursor={
                "op": decision.suggested_op_type,
                "plan": list(decision.process_plan),
                "sheriff": verdict.state.value,
            },
            evidence_hash=decision.fingerprint_hash,
        )

    if not verdict.allow_execute:
        if runtime is not None and mid:
            runtime.complete(mid, ok=False)
        out = format_output(
            {
                "mission_id": mid or "",
                "status": "BLOCKED",
                "summary": "control_pipeline_blocked",
                "goal": goal or "",
                "evidence_hash": decision.fingerprint_hash,
                "set_hash": decision.set_hash,
                "sheriff_state": verdict.state.value,
                "risk_score": decision.risk_score,
                "contracts_active": list(decision.active_contracts),
                "errors": list(verdict.reasons),
                "blocked_reason": ";".join(verdict.reasons),
                "mode": mount_mode,
            }
        )
        return PipelineResult(
            ok=False,
            blocked=True,
            mission_id=mid,
            decision=decision.to_dict(),
            verdict=verdict.to_dict(),
            output=out,
            shadow_id=shadow_rec.record_id if shadow_rec else None,
        )

    if runtime is not None and mid and not verdict.shadow_only:
        runtime.complete(mid, ok=True)

    status = "COMPLETED"
    if verdict.shadow_only:
        status = "RUNNING"  # shadow no cierra prod

    out = format_output(
        {
            "mission_id": mid or "",
            "status": status,
            "summary": "control_pipeline_ok",
            "goal": goal or "",
            "evidence_hash": decision.fingerprint_hash,
            "set_hash": decision.set_hash,
            "sheriff_state": verdict.state.value,
            "risk_score": decision.risk_score,
            "contracts_active": list(decision.active_contracts),
            "mode": mount_mode,
            "steps_done": list(decision.process_plan)[:8],
        }
    )
    return PipelineResult(
        ok=True,
        blocked=False,
        mission_id=mid,
        decision=decision.to_dict(),
        verdict=verdict.to_dict(),
        output=out,
        shadow_id=shadow_rec.record_id if shadow_rec else None,
    )
