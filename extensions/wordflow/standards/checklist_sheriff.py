"""ChecklistSheriff v2 — no self-certification; uses Applicability + EvidenceVerifier."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from .programming_points_catalog import BY_ID, CATALOG_VERSION, core_ids
from .applicability_engine import ApplicabilityEngine, ApplicabilityResult
from .evidence_verifier import EvidenceVerifier, EvidenceRef

@dataclass
class PointClaim:
    point_id: str
    addressed: bool
    evidence: str = ""
    evidence_kind: str = "measure"
    skipped_reason: str = ""

@dataclass
class AgentChecklistClaim:
    mission_id: str
    task_id: str
    catalog_version: str = CATALOG_VERSION
    action: str = "GENERATE"
    sources: List[str] = field(default_factory=list)
    files_touched: List[str] = field(default_factory=list)
    claims: List[PointClaim] = field(default_factory=list)
    # agent may propose non-applicable; engine decides
    proposed_non_applicable: List[str] = field(default_factory=list)
    tags_hint: Dict[str, bool] = field(default_factory=dict)

@dataclass
class SheriffFinding:
    point_id: str
    severity: str
    message: str

@dataclass
class SheriffVerdict:
    passed: bool
    findings: List[SheriffFinding] = field(default_factory=list)
    required_total: int = 0
    required_addressed: int = 0
    coverage_ratio: float = 0.0
    applicability: Optional[Dict[str, Any]] = None
    catalog_version: str = CATALOG_VERSION

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "passed": self.passed,
            "required_total": self.required_total,
            "required_addressed": self.required_addressed,
            "coverage_ratio": self.coverage_ratio,
            "catalog_version": self.catalog_version,
            "findings": [asdict(f) for f in self.findings],
            "applicability": self.applicability,
            "rule": "AGENT_CLAIM_IS_NOT_VERIFICATION",
        }
        return d


class ChecklistSheriff:
    def __init__(self):
        self.app_engine = ApplicabilityEngine()
        self.evidence = EvidenceVerifier()

    def evaluate(self, claim: AgentChecklistClaim) -> SheriffVerdict:
        findings: List[SheriffFinding] = []
        if claim.catalog_version != CATALOG_VERSION:
            findings.append(SheriffFinding("CATALOG", "BLOCK", f"catalog version mismatch {claim.catalog_version} != {CATALOG_VERSION}"))

        appl: ApplicabilityResult = self.app_engine.classify(
            files=claim.files_touched,
            action=claim.action,
            has_external_api=bool(claim.tags_hint.get("external_api")),
            has_db=bool(claim.tags_hint.get("db")),
            has_concurrency=bool(claim.tags_hint.get("concurrency")),
            has_ai_agent=bool(claim.tags_hint.get("ai_agent")),
            has_ui=bool(claim.tags_hint.get("ui")),
            new_dependency=bool(claim.tags_hint.get("new_dep")),
            security_sensitive=bool(claim.tags_hint.get("security")),
            public_api=bool(claim.tags_hint.get("public_api")),
            side_effects=bool(claim.tags_hint.get("side_effects")),
        )
        # Agent cannot downgrade required
        required = list(appl.required_ids)
        for pid in claim.proposed_non_applicable:
            if pid in required:
                findings.append(SheriffFinding(pid, "BLOCK", "AGENT_CANNOT_DOWNGRADE_REQUIRED_CHECK"))

        claimed_map = {c.point_id: c for c in claim.claims}
        addressed = 0
        for pid in required:
            c = claimed_map.get(pid)
            if c is None:
                findings.append(SheriffFinding(pid, "BLOCK", f"required {pid} missing claim"))
                continue
            if not c.addressed:
                findings.append(SheriffFinding(pid, "BLOCK", f"required {pid} not addressed"))
                continue
            ev = self.evidence.verify_ref(EvidenceRef(c.evidence_kind or "measure", c.evidence))
            if not ev.get("ok"):
                findings.append(SheriffFinding(pid, "BLOCK", f"evidence not verified: {ev.get('reason')}"))
                continue
            addressed += 1

        if claim.action in ("COPY", "ADAPT") and not claim.sources:
            findings.append(SheriffFinding("C-CPY-03", "BLOCK", "COPY/ADAPT without sources"))
        if claim.action == "GENERATE":
            c = claimed_map.get("C-CPY-02")
            if not c or not c.addressed:
                findings.append(SheriffFinding("C-CPY-02", "BLOCK", "GENERATE without no-match claim"))

        blocks = [f for f in findings if f.severity == "BLOCK"]
        total = max(len(required), 1)
        return SheriffVerdict(
            passed=len(blocks) == 0,
            findings=findings,
            required_total=len(required),
            required_addressed=addressed,
            coverage_ratio=addressed / total,
            applicability=appl.to_dict(),
        )
