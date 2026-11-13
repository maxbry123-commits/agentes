"""D03 · Research policy · mínimo 20 candidatos por categoría."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, List

DEFAULT_MIN_CANDIDATES = 20


@dataclass
class ResearchCandidate:
    name: str
    url: str = ""
    stars: int = 0
    license: str = ""
    score: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ResearchReport:
    category: str
    candidates: list[ResearchCandidate]
    min_required: int
    ok: bool
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "count": len(self.candidates),
            "min_required": self.min_required,
            "ok": self.ok,
            "reasons": self.reasons,
            "candidates": [c.to_dict() for c in self.candidates],
        }


def evaluate_research(
    *,
    category: str,
    candidates: list[ResearchCandidate] | list[dict],
    min_required: int = DEFAULT_MIN_CANDIDATES,
    skip_min: bool = False,
) -> ResearchReport:
    parsed: list[ResearchCandidate] = []
    for c in candidates:
        if isinstance(c, ResearchCandidate):
            parsed.append(c)
        else:
            parsed.append(
                ResearchCandidate(
                    name=str(c.get("name") or ""),
                    url=str(c.get("url") or ""),
                    stars=int(c.get("stars") or 0),
                    license=str(c.get("license") or ""),
                    score=float(c.get("score") or 0.0),
                    meta=dict(c.get("meta") or {}),
                )
            )
    reasons: list[str] = []
    ok = True
    if not skip_min and len(parsed) < min_required:
        ok = False
        reasons.append(f"below_min:{len(parsed)}<{min_required}")
    # licencia vacía no bloquea score, pero se reporta
    no_license = sum(1 for c in parsed if not c.license)
    if no_license and len(parsed):
        reasons.append(f"missing_license:{no_license}")
    return ResearchReport(
        category=category,
        candidates=parsed,
        min_required=min_required,
        ok=ok,
        reasons=reasons,
    )


def rank_candidates(candidates: list[ResearchCandidate], *, top_n: int = 10) -> list[ResearchCandidate]:
    return sorted(candidates, key=lambda c: (c.score, c.stars), reverse=True)[:top_n]
