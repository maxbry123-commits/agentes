"""forensic.audit capability — unified entry for Wordflow.

Produces EvidencePacket + recommended TaskSpec list from claims/requirements.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from .repo_truth import RepoTruthPort, build_repo_truth
from .forensic import ForensicEngine
from .crosscheck import CrossVerifier, Claim
from .gap_tasks import GapTaskCompiler
from .models import uid, stable_hash


@dataclass
class EvidencePacket:
    packet_id: str
    mission_id: str
    target: str
    revision: str
    status: str
    forensic: dict[str, Any] = field(default_factory=dict)
    crosscheck: dict[str, Any] = field(default_factory=dict)
    recommended_tasks: list[dict[str, Any]] = field(default_factory=list)
    content_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


def forensic_audit(
    target: str,
    requirements: list[dict | str] | None = None,
    claims: list[dict] | None = None,
    mission_id: str = "",
    workspace_id: str = "",
    repo: RepoTruthPort | None = None,
) -> EvidencePacket:
    """Run forensic + optional crosscheck; return packet + tasks."""
    mission_id = mission_id or uid("mission")
    repo = repo or build_repo_truth(target if ":" in target else f"local:{target}")
    eng = ForensicEngine(repo)
    report = eng.audit(target, requirements=requirements or [])
    compiler = GapTaskCompiler()
    tasks = compiler.compile(report, workspace_id or "default")

    cross: dict[str, Any] = {}
    if claims:
        cv = CrossVerifier(repo)
        claim_objs = [
            Claim(
                claim_id=c.get("claim_id", uid("claim")),
                text=c.get("text", ""),
                marker=c.get("marker"),
                path=c.get("path"),
                requirement=c.get("requirement", ""),
            )
            for c in claims
        ]
        raw = cv.verify(claim_objs)
        # serialize ClaimResult
        cross = {
            "claims": raw["claims"],
            "counts": raw["counts"],
            "status": raw["status"],
            "results": [
                {
                    "claim_id": r.claim_id,
                    "status": r.status,
                    "detail": r.detail,
                }
                for r in raw["results"]
            ],
        }

    packet = EvidencePacket(
        packet_id=uid("ep"),
        mission_id=mission_id,
        target=target,
        revision=report.revision,
        status=report.status,
        forensic={
            "audit_id": report.audit_id,
            "matches": report.matches,
            "partial": report.partial,
            "missing": report.missing,
            "gaps": [g.requirement for g in report.gaps],
        },
        crosscheck=cross,
        recommended_tasks=[t.__dict__ for t in tasks],
    )
    packet.content_hash = stable_hash(packet.to_dict())
    return packet
