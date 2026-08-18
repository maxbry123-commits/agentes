"""RuleEngine — rules as executable controls, not labels."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Any
from .schema import StandardContract, RuleId
from .architecture_manifest import ArchitectureManifest, default_wordflow_manifest, scan_file_imports
from .dependency_graph import DependencyGraph
from .evidence import EvidencePacket

class Severity(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"

@dataclass
class Finding:
    rule: str
    severity: Severity
    message: str
    path: Optional[str] = None

@dataclass
class EngineVerdict:
    passed: bool
    findings: List[Finding] = field(default_factory=list)

    @property
    def blocking(self) -> List[Finding]:
        return [f for f in self.findings if f.severity in (Severity.P0, Severity.P1)]

Collector = Callable[[], List[Finding]]

class RuleEngine:
    def __init__(
        self,
        contract: Optional[StandardContract] = None,
        manifest: Optional[ArchitectureManifest] = None,
    ):
        self.contract = contract or StandardContract()
        self.manifest = manifest or default_wordflow_manifest()
        self._collectors: Dict[str, Collector] = {}
        self._register_builtins()

    def register(self, rule_id: str, collector: Collector) -> None:
        self._collectors[rule_id] = collector

    def _register_builtins(self) -> None:
        self.register(RuleId.FILE_LOC.value, self._collect_file_loc)
        self.register(RuleId.NO_CIRCULAR.value, self._collect_cycles)
        self.register(RuleId.NO_FORBIDDEN_IMPORTS.value, self._collect_forbidden_imports)
        self.register(RuleId.EVIDENCE_REQUIRED.value, self._collect_evidence)
        self.register(RuleId.NEVER_MVP.value, self._collect_never_mvp)
        self.register(RuleId.GAPS_100.value, self._collect_gaps)
        self.register(RuleId.AI_NOT_PROOF.value, self._collect_ai_proof)

    # context injected before evaluate
    file_locs: Dict[str, int] = field(default_factory=dict) if False else {}
    scan_paths: List[Path] = field(default_factory=list) if False else []
    evidence: Optional[EvidencePacket] = None
    claim_mvp: bool = False
    gaps_blocking: int = 0  # only P0/P1 count
    used_ai_as_proof: bool = False

    def __init_context(self, **kwargs: Any) -> None:
        self.file_locs = kwargs.get("file_locs") or {}
        self.scan_paths = kwargs.get("scan_paths") or []
        self.evidence = kwargs.get("evidence")
        self.claim_mvp = bool(kwargs.get("claim_mvp", False))
        self.gaps_blocking = int(kwargs.get("gaps_blocking", 0))
        self.used_ai_as_proof = bool(kwargs.get("used_ai_as_proof", False))

    def _collect_file_loc(self) -> List[Finding]:
        out: List[Finding] = []
        for p, loc in self.file_locs.items():
            if loc > 1500:
                out.append(Finding(RuleId.FILE_LOC.value, Severity.P0, f"LOC={loc}>1500", p))
            elif loc > 1000:
                out.append(Finding(RuleId.FILE_LOC.value, Severity.P1, f"LOC={loc}>1000 refactor", p))
            elif loc > 800:
                out.append(Finding(RuleId.FILE_LOC.value, Severity.P2, f"LOC={loc}>800 review", p))
            # <300 is preferred-min soft: P2 info only if explicitly flagged
        return out

    def _collect_cycles(self) -> List[Finding]:
        if not self.scan_paths:
            return []
        g = DependencyGraph()
        g.build_from_paths(self.scan_paths)
        cycles = g.find_cycles_module_level()
        return [
            Finding(RuleId.NO_CIRCULAR.value, Severity.P0, f"cycle={c}", None)
            for c in cycles
        ]

    def _collect_forbidden_imports(self) -> List[Finding]:
        if not self.scan_paths:
            return []
        g = DependencyGraph()
        g.build_from_paths(self.scan_paths)
        forbidden = list(self.manifest.forbidden_global_imports)
        hits = g.forbidden_hits(forbidden)
        return [
            Finding(RuleId.NO_FORBIDDEN_IMPORTS.value, Severity.P0, f"import {imp}", f)
            for f, imp in hits
        ]

    def _collect_evidence(self) -> List[Finding]:
        if self.evidence is None:
            return []  # only enforced when evidence context is required by caller
        if not self.evidence.is_complete():
            return [Finding(RuleId.EVIDENCE_REQUIRED.value, Severity.P0, "EvidencePacket incomplete")]
        return []

    def _collect_never_mvp(self) -> List[Finding]:
        if self.claim_mvp and self.contract.never_mvp:
            return [Finding(RuleId.NEVER_MVP.value, Severity.P0, "MVP claim forbidden")]
        return []

    def _collect_gaps(self) -> List[Finding]:
        # Only blocking gaps (P0/P1). P2 debt allowed.
        if self.gaps_blocking > 0 and self.contract.gaps_must_be_100:
            return [Finding(
                RuleId.GAPS_100.value,
                Severity.P0,
                f"blocking gaps open={self.gaps_blocking}",
            )]
        return []

    def _collect_ai_proof(self) -> List[Finding]:
        if self.used_ai_as_proof and self.contract.ai_output_is_not_proof:
            return [Finding(RuleId.AI_NOT_PROOF.value, Severity.P0, "AI output is not proof")]
        return []

    def evaluate(self, **kwargs: Any) -> EngineVerdict:
        self.__init_context(**kwargs)
        findings: List[Finding] = []
        for rule_id, collector in self._collectors.items():
            findings.extend(collector())
        blocking = [f for f in findings if f.severity in (Severity.P0, Severity.P1)]
        return EngineVerdict(passed=len(blocking) == 0, findings=findings)
