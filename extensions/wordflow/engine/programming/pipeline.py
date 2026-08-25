"""Wordflow programming pipeline — UNIFIED + U2 kwargs + U7 single PreGate."""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Optional, Set
from extensions.wordflow.standards.executor_gates import ExecutorPreImplementGate, ExecutorPostVerifyGate
from extensions.wordflow.standards.forensic_contract import ForensicCodeContract
from extensions.wordflow.standards.evidence import EvidencePacket
from extensions.wordflow.standards.copy_first import ExistingCodeScanner, copy_file_deterministic
from extensions.wordflow.standards.path_resolve import default_scan_roots
from extensions.wordflow.standards.policy_snapshot import PolicySnapshot

KERNEL_ROOT = Path(__file__).resolve().parents[3] / "wordflow_kernel"

KNOWN_KW: Set[str] = {
    "context_verified", "handoff_verified", "symbol_or_stem", "dest", "checklist",
    "require_pre_gate", "require_checklist", "mission_id", "core_measures", "connectivity",
    "counters", "evidence_complete", "final_clean_reaudit_passed", "quality_dag_ok",
    "context_manifest", "require_context_manifest", "fc_results", "require_fc",
    "auto_measure_core", "auto_measure_fc", "apply_adapt", "import_mapping", "profile",
    "scan_paths", "plan_steps", "skill", "run_quality_dag", "pre_gate_done",
}


class ProgrammingPipeline:
    def __init__(self):
        roots = default_scan_roots()
        if KERNEL_ROOT.exists():
            roots.append(KERNEL_ROOT)
        self.pre = ExecutorPreImplementGate(scan_roots=roots)
        self.post = ExecutorPostVerifyGate()
        self.scanner = ExistingCodeScanner(roots)

    def pre_implement(self, *, context_verified: bool, handoff_verified: bool, symbol_or_stem: str, dest: str, checklist=None, require_checklist: bool = True) -> Dict[str, Any]:
        return self.pre.check(context_verified=context_verified, handoff_verified=handoff_verified, symbol_or_stem=symbol_or_stem, dest=dest, checklist=checklist, require_checklist=require_checklist)

    def copy_existing(self, src: str, dest: str) -> Dict[str, Any]:
        return copy_file_deterministic(Path(src), Path(dest))

    def post_verify(self, contract: ForensicCodeContract, evidence: Optional[EvidencePacket] = None, checklist=None, require_checklist: bool = True) -> Dict[str, Any]:
        return self.post.verify(contract, evidence, checklist=checklist, require_checklist=require_checklist)

    def run_unified(self, raw_input: str, **kwargs: Any) -> Dict[str, Any]:
        from extensions.wordflow.engine.programming.runner import run_code_path

        unknown = sorted(k for k in kwargs if k not in KNOWN_KW and not k.startswith("_"))
        if unknown:
            return {
                "ok": False,
                "stage": "kwargs",
                "detail": f"U2 unknown kwargs: {unknown}",
                "verdict": "BLOCK",
                "llm_control": "DENY",
                "path": "UNIFIED_PIPELINE_V1_MODULAR",
            }

        context_verified = bool(kwargs.get("context_verified", False))
        handoff_verified = bool(kwargs.get("handoff_verified", False))
        symbol_or_stem = str(kwargs.get("symbol_or_stem", "") or "")
        dest = str(kwargs.get("dest", "") or "")
        checklist = kwargs.get("checklist")
        require_pre_gate = bool(kwargs.get("require_pre_gate", False))
        require_checklist = bool(kwargs.get("require_checklist", False))
        mission_id = str(kwargs.get("mission_id", "") or "")
        pre_gate_done = bool(kwargs.get("pre_gate_done", False))

        stages: Dict[str, Any] = {}
        snap = PolicySnapshot.freeze(mission_id or "unified")
        stages["policy_snapshot"] = {
            "mission_id": snap.mission_id,
            "contract_version": snap.contract_version,
            "frozen_at": snap.frozen_at,
        }

        if require_pre_gate and symbol_or_stem and dest and not pre_gate_done:
            pre = self.pre_implement(
                context_verified=context_verified,
                handoff_verified=handoff_verified,
                symbol_or_stem=symbol_or_stem,
                dest=dest,
                checklist=checklist,
                require_checklist=require_checklist,
            )
            stages["pre_gate"] = pre
            if not pre.get("allow"):
                return {
                    "ok": False,
                    "stage": "pre_gate",
                    "stages": stages,
                    "verdict": "BLOCK",
                    "llm_control": "DENY",
                    "path": "UNIFIED_PIPELINE_V1_MODULAR",
                    "policy": stages["policy_snapshot"],
                }
            pre_gate_done = True

        runner_kwargs = {k: v for k, v in kwargs.items() if not k.startswith("_") and k != "pre_gate_done"}
        if pre_gate_done:
            runner_kwargs["symbol_or_stem"] = ""
            runner_kwargs["dest"] = ""
            runner_kwargs["require_pre_gate"] = False

        runner = run_code_path(raw_input, **runner_kwargs)
        stages["runner"] = runner
        ok = bool(runner.get("ok"))
        return {
            "ok": ok,
            "stages": stages,
            "verdict": runner.get("verdict"),
            "forensic": runner.get("forensic"),
            "closure": runner.get("closure"),
            "gaps": runner.get("gaps"),
            "wire_trace": runner.get("wire_trace"),
            "policy": stages["policy_snapshot"],
            "llm_control": "DENY",
            "path": "UNIFIED_PIPELINE_V1_MODULAR",
            "c_status": runner.get("c_status"),
            "s_status": runner.get("s_status"),
            "t_status": runner.get("t_status", "T1-T8_CLOSED"),
            "u_status": "U1-U10_CLOSED",
            "modular": True,
        }


def default_pipeline() -> ProgrammingPipeline:
    return ProgrammingPipeline()
