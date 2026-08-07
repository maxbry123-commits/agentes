"""Entrypoint Wordflow · cara de trabajo del núcleo dual.

Uso programático:
  app = WordflowApp(state_dir)
  result = app.run_mission(goal, op_type="WRITE_LOCAL", payload={...})

CLI:
  python -m wordflow.entrypoint --goal "..." --state-dir ./state [--confirm-critical]
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from contract_engine.sentinela_router import route
from extension.abi import WordflowExtension
from format.output_chef import format_output
from inputblock.critical_gate import CriticalConfirmRequired, check_critical_confirm
from inputblock.store import Criticality, InputStore
from loops.correction_set import apply_correction
from runtime.durable import DurableRuntime
from sheriff.gate import run_sheriff


@dataclass
class MissionResult:
    mission_id: str
    ok: bool
    output: dict[str, Any]
    sheriff_state: str
    blocked: bool
    evidence_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class WordflowApp:
    def __init__(self, state_dir: Path, *, input_store: InputStore | None = None) -> None:
        self.runtime = DurableRuntime(Path(state_dir))
        self.store = input_store or InputStore()
        self.ext = WordflowExtension()
        self.ext.load({"mount_mode": "wordflow"})

    def run_mission(
        self,
        goal: str,
        *,
        op_type: str = "READ_LOCAL",
        payload: Mapping[str, Any] | None = None,
        mission_id: str | None = None,
        nivel: str = "MID",
        criticality: Criticality = Criticality.ORDEN,
        confirm_critical: bool = False,
    ) -> MissionResult:
        state = self.runtime.create_mission(goal, mission_id=mission_id)
        self.store.append(
            goal,
            criticality=criticality,
            mission_id=state.mission_id,
        )

        # Gate B03: CRITICO sin confirm → no arranca
        try:
            check_critical_confirm(
                list(self.store),
                confirmed=confirm_critical,
                raise_on_block=True,
            )
        except CriticalConfirmRequired as ex:
            self.runtime.checkpoint(
                state.mission_id,
                phase="blocked_critical",
                cursor={"op": op_type},
                evidence_hash="sha256:critical_confirm",
            )
            self.runtime.complete(state.mission_id, ok=False)
            out = format_output(
                {
                    "mission_id": state.mission_id,
                    "status": "BLOCKED",
                    "summary": "critical_confirm_required",
                    "goal": goal,
                    "evidence_hash": "sha256:critical_confirm",
                    "sheriff_state": "RED",
                    "errors": [str(ex)],
                    "blocked_reason": str(ex),
                    "mode": "wordflow",
                }
            )
            return MissionResult(
                mission_id=state.mission_id,
                ok=False,
                output=out,
                sheriff_state="RED",
                blocked=True,
                evidence_hash="sha256:critical_confirm",
            )

        decision = route(
            op_type=op_type,
            payload=payload or {"goal": goal},
            mount_mode="wordflow",
            strict_reverse=False,
        )
        verdict, _ = run_sheriff(decision.to_dict())

        if not verdict.allow_execute:
            self.runtime.checkpoint(
                state.mission_id,
                phase="blocked",
                cursor={"op": op_type},
                evidence_hash=decision.fingerprint_hash,
            )
            self.runtime.complete(state.mission_id, ok=False)
            out = format_output(
                {
                    "mission_id": state.mission_id,
                    "status": "BLOCKED",
                    "summary": "sheriff_blocked",
                    "goal": goal,
                    "evidence_hash": decision.fingerprint_hash,
                    "set_hash": decision.set_hash,
                    "sheriff_state": verdict.state.value,
                    "risk_score": decision.risk_score,
                    "contracts_active": list(decision.active_contracts),
                    "errors": list(verdict.reasons),
                    "blocked_reason": ";".join(verdict.reasons),
                    "mode": "wordflow",
                }
            )
            return MissionResult(
                mission_id=state.mission_id,
                ok=False,
                output=out,
                sheriff_state=verdict.state.value,
                blocked=True,
                evidence_hash=decision.fingerprint_hash,
            )

        self.runtime.checkpoint(
            state.mission_id,
            phase="ejecutar",
            cursor={"op": op_type, "plan": list(decision.process_plan)},
            evidence_hash=decision.fingerprint_hash,
        )
        ev = self.ext.execute(
            "route_op",
            {"op_type": op_type, "payload": dict(payload or {"goal": goal})},
            nivel=nivel,
        )
        self.runtime.complete(state.mission_id, ok=ev.ok)
        out = format_output(
            {
                "mission_id": state.mission_id,
                "status": "COMPLETED" if ev.ok else "FAILED",
                "summary": "mission_finished",
                "goal": goal,
                "evidence_hash": ev.evidence_hash or decision.fingerprint_hash,
                "set_hash": ev.set_hash or decision.set_hash,
                "sheriff_state": verdict.state.value,
                "risk_score": decision.risk_score,
                "contracts_active": list(decision.active_contracts),
                "mode": "wordflow",
                "steps_done": ["critical_gate", "route", "sheriff", "execute"],
            }
        )
        return MissionResult(
            mission_id=state.mission_id,
            ok=ev.ok,
            output=out,
            sheriff_state=verdict.state.value,
            blocked=False,
            evidence_hash=out.get("evidence_hash") or "",
        )

    def correct(self, mission_id: str, content: str) -> dict[str, Any]:
        r = apply_correction(
            runtime=self.runtime,
            mission_id=mission_id,
            content=content,
            store=self.store,
        )
        return r.to_dict()


def run_mission(goal: str, state_dir: str | Path, **kwargs: Any) -> MissionResult:
    return WordflowApp(Path(state_dir)).run_mission(goal, **kwargs)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="wordflow")
    p.add_argument("--goal", required=True)
    p.add_argument("--state-dir", default="./wordflow_state")
    p.add_argument("--op-type", default="READ_LOCAL")
    p.add_argument("--nivel", default="MID")
    p.add_argument("--confirm-critical", action="store_true")
    p.add_argument("--critical", action="store_true", help="marca input como CRITICO")
    args = p.parse_args(argv)
    crit = Criticality.CRITICO if args.critical else Criticality.ORDEN
    result = run_mission(
        args.goal,
        args.state_dir,
        op_type=args.op_type,
        nivel=args.nivel,
        criticality=crit,
        confirm_critical=args.confirm_critical,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
