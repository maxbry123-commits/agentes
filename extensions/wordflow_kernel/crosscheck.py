"""CrossVerifier — claim vs repo evidence (deterministic rules)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .repo_truth import RepoTruthPort
from .models import Evidence, uid


@dataclass
class Claim:
    claim_id: str
    text: str
    marker: str | None = None
    path: str | None = None
    requirement: str = ""


@dataclass
class ClaimResult:
    claim_id: str
    status: str  # IMPLEMENTED | PARTIAL | MISSING | CONTRADICTED | UNVERIFIED
    evidence: list[Evidence] = field(default_factory=list)
    detail: dict[str, Any] = field(default_factory=dict)


class CrossVerifier:
    def __init__(self, repo: RepoTruthPort):
        self.repo = repo

    def _load_texts(self) -> dict[str, str]:
        texts = {}
        for f in self.repo.list_files():
            try:
                texts[f.path] = self.repo.read_file(f.path).decode("utf-8", "ignore")
            except Exception:
                texts[f.path] = ""
        return texts

    def verify_one(self, claim: Claim, texts: dict[str, str] | None = None) -> ClaimResult:
        texts = texts if texts is not None else self._load_texts()
        marker = claim.marker or claim.requirement or claim.text
        evidence: list[Evidence] = []

        if claim.path:
            if claim.path not in texts:
                return ClaimResult(
                    claim.claim_id,
                    "MISSING",
                    detail={"reason": "path_not_found", "path": claim.path},
                )
            content = texts[claim.path]
            evidence.append(
                Evidence(uid("ev"), "file", claim.path, detail={"marker": marker})
            )
            if marker and marker in content:
                return ClaimResult(claim.claim_id, "IMPLEMENTED", evidence)
            # path exists but marker missing → PARTIAL
            return ClaimResult(
                claim.claim_id,
                "PARTIAL",
                evidence,
                detail={"reason": "path_exists_marker_missing"},
            )

        # search all files
        hits = [p for p, c in texts.items() if marker and marker in c]
        if hits:
            for p in hits[:5]:
                evidence.append(Evidence(uid("ev"), "file", p, detail={"marker": marker}))
            return ClaimResult(claim.claim_id, "IMPLEMENTED", evidence)

        return ClaimResult(
            claim.claim_id,
            "MISSING",
            detail={"reason": "marker_not_found", "marker": marker},
        )

    def verify(self, claims: list[Claim]) -> dict[str, Any]:
        texts = self._load_texts()
        results = [self.verify_one(c, texts) for c in claims]
        counts = {"IMPLEMENTED": 0, "PARTIAL": 0, "MISSING": 0, "CONTRADICTED": 0, "UNVERIFIED": 0}
        for r in results:
            counts[r.status] = counts.get(r.status, 0) + 1
        return {
            "claims": len(claims),
            "counts": counts,
            "results": results,
            "status": "PASS" if counts["MISSING"] == 0 and counts["PARTIAL"] == 0 else "GAPS_FOUND",
        }
