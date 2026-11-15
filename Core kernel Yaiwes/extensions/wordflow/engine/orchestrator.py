# -*- coding: utf-8 -*-
"""Orchestrator — T47. Thin glue State+Mission+Brain+Panel. 0% LLM."""
from __future__ import annotations

from typing import Any

from .bootstrap import WordflowKernel
from .capability_brain import CapabilityBrain
from .expert_router import route_and_decide
from .mission import enforce_mission, mission_from_raw
from .state_authority import StateAuthority, SystemState


class Orchestrator:
    def __init__(self, kernel: WordflowKernel | None = None):
        self.kernel = kernel or WordflowKernel()
        self.state = StateAuthority()
        self.brain = CapabilityBrain(registry=self.kernel.registry)

    def start(self) -> dict[str, Any]:
        kr = self.kernel.start()
        self.brain = CapabilityBrain(registry=self.kernel.registry)
        return {"ok": True, "kernel": kr, "state": self.state.snapshot()}

    def run_turn(
        self,
        raw_input: str,
        topic: str,
        *,
        risk_score: int = 0,
        band: str = "",
        task_class: str | None = None,
    ) -> dict[str, Any]:
        if not self.kernel.started:
            self.start()

        # build phase
        self.state.transition(SystemState.CONSTRUIR, reason="turn_start")
        mission = mission_from_raw(raw_input)
        if not mission.get("ok"):
            self.state.transition(SystemState.REPAIR, reason="mission_fail")
            return {"ok": False, "stage": "mission", "detail": mission, "state": self.state.snapshot()}

        self.state.transition(SystemState.VALIDAR, reason="enforce")
        enforced = enforce_mission(mission, risk_score=risk_score, band=band)
        if not enforced.get("ok"):
            self.state.transition(SystemState.DETENIDO, reason="sheriff_deny")
            return {
                "ok": False,
                "stage": "sheriff",
                "enforced": enforced,
                "state": self.state.snapshot(),
            }

        self.state.transition(SystemState.AUDITAR, reason="brain_panel")
        brain = self.brain.run(topic or raw_input, task_class=task_class)
        panel = route_and_decide(
            topic,
            task_class=task_class or "DEFAULT",
            context={"risk_score": risk_score},
        )

        if not panel.get("ok"):
            self.state.transition(SystemState.REPAIR, reason="panel_deny")
        else:
            self.state.transition(SystemState.ESPERAR_APROBACION, reason="panel_allow")

        return {
            "ok": bool(panel.get("ok")),
            "stage": "turn_done",
            "mission_id": mission.get("mission_id"),
            "enforced": enforced,
            "brain": brain,
            "panel": panel,
            "state": self.state.snapshot(),
        }
