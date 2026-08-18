"""Wordflow programming pipeline — CONTEXT→COPY-FIRST→IMPLEMENT→FORENSIC→VERDICT.
UNIFIED: PreGate (COPY-FIRST+Sheriff) + run_code_path (forensic_core CORE14).
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Optional, List
from extensions.wordflow.standards.executor_gates import ExecutorPreImplementGate, ExecutorPostVerifyGate
from extensions.wordflow.standards.forensic_contract import ForensicCodeContract, CoreChecks, AuditPasses, ClosureCounters
from extensions.wordflow.standards.evidence import EvidencePacket
from extensions.wordflow.standards.copy_first import ExistingCodeScanner, copy_file_deterministic

WF_ROOT = Path(__file__).resolve().parents[1]
KERNEL_ROOT = Path(__file__).resolve().parents[2] / "wordflow_kernel"

class ProgrammingPipeline:
    def __init__(self):
        roots = [WF_ROOT, KERNEL_ROOT]
        self.pre = ExecutorPreImplementGate(scan_roots=roots)
        self.post = ExecutorPostVerifyGate()
        self.scanner = ExistingCodeScanner(roots)

    def pre_implement(
        self,
        *,
        context_verified: bool,
        handoff_verified: bool,
        symbol_or_stem: str,
        dest: str,
        checklist=None,
        require_checklist: bool = True,
    ) -> Dict[str, Any]:
        return self.pre.check(
            context_verified=context_verified,
            handoff_verified=handoff_verified,
            symbol_or_stem=symbol_or_stem,
            dest=dest,
            checklist=checklist,
            require_checklist=require_checklist,
        )

    def copy_existing(self, src: str, dest: str) -> Dict[str, Any]:
        return copy_file_deterministic(Path(src), Path(dest))

    def post_verify(
        self,
        contract: ForensicCodeContract,
        evidence: Optional[EvidencePacket] = None,
        checklist=None,
        require_checklist: bool = True,
    ) -> Dict[str, Any]:
        return self.post.verify(contract, evidence, checklist=checklist, require_checklist=require_checklist)

    def run_unified(
        self,
        raw_input: str,
        *,
        context_verified: bool = False,
        handoff_verified: bool = False,
        symbol_or_stem: str = "",
        dest: str = "",
        checklist=None,
        require_pre_gate: bool = True,
        require_checklist: bool = False,
        mission_id: str = "",
        core_measures: Optional[Dict[str, bool]] = None,
        connectivity: Optional[Dict[str, bool]] = None,
        counters: Optional[Dict[str, int]] = None,
        evidence_complete: bool = False,
        final_clean_reaudit_passed: bool = False,
        quality_dag_ok: bool = False,
        context_manifest=None,
        require_context_manifest: bool = False,
        fc_results: Optional[Dict[str, bool]] = None,
    ) -> Dict[str, Any]:
        """GC-09/10/12: un solo path PreGate + forensic runner + post optional."""
        from extensions.wordflow.engine.code_path_runner import run_code_path

        stages: Dict[str, Any] = {}
        if require_pre_gate and symbol_or_stem and dest:
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
                    "path": "UNIFIED_PIPELINE_V1",
                }

        runner = run_code_path(
            raw_input,
            mission_id=mission_id,
            context_verified=context_verified,
            handoff_verified=handoff_verified,
            core_measures=core_measures,
            connectivity=connectivity,
            counters=counters,
            evidence_complete=evidence_complete,
            final_clean_reaudit_passed=final_clean_reaudit_passed,
            quality_dag_ok=quality_dag_ok,
            context_manifest=context_manifest,
            require_context_manifest=require_context_manifest,
            symbol_or_stem=symbol_or_stem if not require_pre_gate else "",
            dest=dest if not require_pre_gate else "",
            checklist=checklist,
            require_pre_gate=False,  # already done above when required
            require_checklist=False,
            fc_results=fc_results,
        )
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
            "llm_control": "DENY",
            "path": "UNIFIED_PIPELINE_V1",
        }

def default_pipeline() -> ProgrammingPipeline:
    return ProgrammingPipeline()
