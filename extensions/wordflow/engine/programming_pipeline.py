"""Wordflow programming pipeline — CONTEXT→COPY-FIRST→IMPLEMENT→FORENSIC→VERDICT.
Cableado ejecutor real (mejora G-W1).
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
    ) -> Dict[str, Any]:
        return self.pre.check(
            context_verified=context_verified,
            handoff_verified=handoff_verified,
            symbol_or_stem=symbol_or_stem,
            dest=dest,
        )

    def copy_existing(self, src: str, dest: str) -> Dict[str, Any]:
        return copy_file_deterministic(Path(src), Path(dest))

    def post_verify(
        self,
        contract: ForensicCodeContract,
        evidence: Optional[EvidencePacket] = None,
    ) -> Dict[str, Any]:
        return self.post.verify(contract, evidence)

def default_pipeline() -> ProgrammingPipeline:
    return ProgrammingPipeline()
