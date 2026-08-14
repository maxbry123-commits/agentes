# -*- coding: utf-8 -*-
"""OrchestratorV1 — V1-01. Single path wire for Wordflow V1. 0% LLM.

mission → gate_c00 → contract_router → panel → dna → evidence
Fail-closed at each stage. No real engines / network.
"""
from __future__ import annotations

from typing import Any

from .bootstrap import WordflowKernel
from .capability_brain import CapabilityBrain
from .contract_router import ContractRouter
from .control_sheriff_bridge import gate_c00
from .evidence_graph import EvidenceGraph
from .expert_router import route_and_decide
from .mission import enforce_mission, mission_from_raw
from .state_authority import StateAuthority, SystemState
from .workflow_dna import compile_dna, verify_dna


class OrchestratorV1:
    def __init__(self, kernel: WordflowKernel | None = None):
        self.kernel = kernel or WordflowKernel()
        self.state = StateAuthority()
        self.router = ContractRouter()
        self.brain = CapabilityBrain(registry=self.kernel.registry)
        self.evidence = EvidenceGraph()

    def start(self) -> dict[str, Any]:
        kr = self.kernel.start()
        self.brain = CapabilityBrain(registry=self.kernel.registry)
        return {"ok": True, "kernel": kr, "state": self.state.snapshot()}

    def run_turn(
        self,
        raw_input: str,
        topic: str,
        *,
        operation: str = "READ_LOCAL",
        risk_score: int = 0,
        band: str = "",
        task_class: str | None = None,
        require_c00: bool = True,
    ) -> dict[str, Any]:
        if not self.kernel.started:
            self.start()

        self.state.transition(SystemState.CONSTRUIR, reason="v1_turn_start")
        mission = mission_from_raw(raw_input)
        if not mission.get("ok"):
            self.state.transition(SystemState.REPAIR, reason="mission_fail")
            return self._fail("mission", mission)

        lock = mission["lock"]
        self.evidence = EvidenceGraph(mission_id=mission.get("mission_id"))
        n_mission = self.evidence.add_node("mission", mission.get("mission_id"))

        # Sheriff base enforce
        self.state.transition(SystemState.VALIDAR, reason="enforce_mission")
        enforced = enforce_mission(mission, risk_score=risk_score, band=band)
        if not enforced.get("ok"):
            self.state.transition(SystemState.DETENIDO, reason="sheriff_deny")
            self.evidence.add_node("sheriff_deny", enforced, ref_id=n_mission["node_id"])
            return self._fail("sheriff", enforced, mission_id=mission.get("mission_id"))

        # Contract select
        selected = self.router.select(operation, include_c00=True)
        if not selected.get("ok"):
            self.state.transition(SystemState.REPAIR, reason="bad_operation")
            return self._fail("contracts", selected, mission_id=mission.get("mission_id"))

        contracts = list(selected["contracts"])
        n_contracts = self.evidence.add_node("contracts", contracts)
        self.evidence.link(n_mission["node_id"], n_contracts["node_id"], rel="uses")

        # C00 gate (Wordflow path; control-layer optional)
        c00 = gate_c00(
            lock,
            contracts=contracts,
            risk_score=risk_score,
            band=band,
            require_c00=require_c00,
            prefer_control_layer=False,
        )
        if not c00.get("passed"):
            self.state.transition(SystemState.DETENIDO, reason="c00_deny")
            self.evidence.add_node("c00_deny", c00)
            return self._fail("c00", c00, mission_id=mission.get("mission_id"))

        n_c00 = self.evidence.add_node("c00_allow", c00.get("action"))
        self.evidence.link(n_contracts["node_id"], n_c00["node_id"], rel="gated")

        # Brain + panel (YAIWES decide)
        self.state.transition(SystemState.AUDITAR, reason="brain_panel")
        brain = self.brain.run(topic or raw_input, task_class=task_class)
        panel = route_and_decide(
            topic or raw_input,
            task_class=task_class or "DEFAULT",
            context={"risk_score": risk_score, "operation": operation},
        )
        if not panel.get("ok"):
            self.state.transition(SystemState.REPAIR, reason="panel_deny")
            self.evidence.add_node("panel_deny", panel)
            return {
                "ok": False,
                "stage": "panel",
                "mission_id": mission.get("mission_id"),
                "enforced": enforced,
                "contracts": selected,
                "c00": c00,
                "brain": brain,
                "panel": panel,
                "evidence": self.evidence.snapshot(),
                "state": self.state.snapshot(),
            }

        n_panel = self.evidence.add_node("panel_allow", panel.get("decision") or "ALLOW")
        self.evidence.link(n_c00["node_id"], n_panel["node_id"], rel="next")

        # DNA
        dna = compile_dna(
            lock,
            workflow_version="1.0",
            policies={"operation": operation, "contracts": contracts},
            success_criteria=["panel_ok", "c00_ok", "mission_ok"],
        )
        dv = verify_dna(dna)
        if not dv.get("ok"):
            self.state.transition(SystemState.REPAIR, reason="dna_fail")
            return self._fail("dna", dv, mission_id=mission.get("mission_id"))

        n_dna = self.evidence.add_node("dna", dna["dna_id"])
        self.evidence.link(n_panel["node_id"], n_dna["node_id"], rel="fingerprint")

        self.state.transition(SystemState.ESPERAR_APROBACION, reason="v1_turn_ok")
        return {
            "ok": True,
            "stage": "v1_turn_done",
            "mission_id": mission.get("mission_id"),
            "enforced": enforced,
            "contracts": selected,
            "c00": c00,
            "brain": brain,
            "panel": panel,
            "dna": dna,
            "evidence": self.evidence.snapshot(),
            "state": self.state.snapshot(),
        }

    def _fail(
        self,
        stage: str,
        detail: dict[str, Any],
        *,
        mission_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            "ok": False,
            "stage": stage,
            "mission_id": mission_id,
            "detail": detail,
            "evidence": self.evidence.snapshot(),
            "state": self.state.snapshot(),
        }
