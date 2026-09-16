from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping
from urllib.parse import urlparse


class ReuseDecision(str, Enum):
    REUSE = "REUSE"
    PATCH = "PATCH"
    ADAPT = "ADAPT"
    GENERATE = "GENERATE"
    RESEARCH_MORE = "RESEARCH_MORE"


class CatalogValidationError(ValueError):
    pass


_COMPAT = {"NATIVE": 50, "HIGH": 35, "MEDIUM": 20, "LOW": 5, "NONE": -100}
_MAINT = {"CURRENT_LOCAL": 20, "ACTIVE": 15, "MAINTAINED": 10, "UNKNOWN": 0, "STALE": -20}
_RISK = {"LOW": 20, "MEDIUM": 5, "HIGH": -30, "UNKNOWN": -10}
_FOOTPRINT = {"SMALL": 15, "MEDIUM": 8, "LARGE": 0, "UNKNOWN": -5}


@dataclass(frozen=True)
class ReuseCandidate:
    candidate_id: str
    name: str
    source_url: str
    license: str
    maintenance: str
    compatibility: str
    risk: str
    footprint: str
    capabilities: tuple[str, ...]
    local: bool = False
    patchable: bool = False
    notes: str = ""

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> "ReuseCandidate":
        required = (
            "candidate_id", "name", "source_url", "license", "maintenance",
            "compatibility", "risk", "footprint", "capabilities",
        )
        missing = [key for key in required if key not in data]
        if missing:
            raise CatalogValidationError(f"missing fields: {','.join(missing)}")
        source_url = str(data["source_url"]).strip()
        parsed = urlparse(source_url)
        if parsed.scheme not in {"https", "http"} or not parsed.netloc:
            raise CatalogValidationError("source_url must be absolute http(s)")
        caps_raw = data["capabilities"]
        if not isinstance(caps_raw, (list, tuple)) or not caps_raw:
            raise CatalogValidationError("capabilities must be a non-empty list")
        caps = tuple(sorted({str(x).strip().lower() for x in caps_raw if str(x).strip()}))
        if not caps:
            raise CatalogValidationError("capabilities cannot normalize to empty")
        maintenance = str(data["maintenance"]).upper()
        compatibility = str(data["compatibility"]).upper()
        risk = str(data["risk"]).upper()
        footprint = str(data["footprint"]).upper()
        if compatibility not in _COMPAT:
            raise CatalogValidationError(f"unsupported compatibility={compatibility}")
        if maintenance not in _MAINT:
            raise CatalogValidationError(f"unsupported maintenance={maintenance}")
        if risk not in _RISK:
            raise CatalogValidationError(f"unsupported risk={risk}")
        if footprint not in _FOOTPRINT:
            raise CatalogValidationError(f"unsupported footprint={footprint}")
        if not str(data["license"]).strip():
            raise CatalogValidationError("license is required")
        return cls(
            candidate_id=str(data["candidate_id"]).strip(),
            name=str(data["name"]).strip(),
            source_url=source_url,
            license=str(data["license"]).strip(),
            maintenance=maintenance,
            compatibility=compatibility,
            risk=risk,
            footprint=footprint,
            capabilities=caps,
            local=bool(data.get("local", False)),
            patchable=bool(data.get("patchable", False)),
            notes=str(data.get("notes", "")).strip(),
        )

    def score(self, requested_capability: str) -> int:
        capability = requested_capability.strip().lower()
        capability_match = 60 if capability in self.capabilities else 0
        local_bonus = 25 if self.local else 0
        return (
            capability_match
            + _COMPAT[self.compatibility]
            + _MAINT[self.maintenance]
            + _RISK[self.risk]
            + _FOOTPRINT[self.footprint]
            + local_bonus
        )


@dataclass(frozen=True)
class SelectionResult:
    requested_capability: str
    decision: ReuseDecision
    candidate_id: str | None
    score: int | None
    reason: str
    ranked: tuple[tuple[str, int], ...]


def validate_catalog(items: Iterable[Mapping[str, object]]) -> tuple[ReuseCandidate, ...]:
    candidates = tuple(ReuseCandidate.from_mapping(item) for item in items)
    ids = [c.candidate_id for c in candidates]
    if len(ids) != len(set(ids)):
        raise CatalogValidationError("duplicate candidate_id")
    if len(candidates) > 10:
        raise CatalogValidationError("catalog exceeds 10 candidates")
    return candidates


def select_reuse(requested_capability: str, candidates: Iterable[ReuseCandidate]) -> SelectionResult:
    capability = requested_capability.strip().lower()
    if not capability:
        raise CatalogValidationError("requested_capability is required")
    matched = [c for c in candidates if capability in c.capabilities]
    if not matched:
        return SelectionResult(
            requested_capability=capability,
            decision=ReuseDecision.GENERATE,
            candidate_id=None,
            score=None,
            reason="NO_MATCHING_CANDIDATE_AFTER_RESEARCH",
            ranked=(),
        )
    ranked_candidates = sorted(
        ((c, c.score(capability)) for c in matched),
        key=lambda pair: (-pair[1], pair[0].candidate_id),
    )
    best, score = ranked_candidates[0]
    ranked = tuple((c.candidate_id, s) for c, s in ranked_candidates)
    if best.risk == "HIGH" or best.compatibility == "NONE":
        return SelectionResult(
            capability, ReuseDecision.RESEARCH_MORE, best.candidate_id, score,
            "TOP_CANDIDATE_FAILS_RISK_OR_COMPATIBILITY_GATE", ranked,
        )
    if best.local and best.compatibility == "NATIVE":
        decision = ReuseDecision.REUSE
        reason = "LOCAL_NATIVE_CAPABILITY_AVAILABLE"
    elif best.local and best.patchable:
        decision = ReuseDecision.PATCH
        reason = "LOCAL_PARTIAL_CAPABILITY_PATCHABLE"
    else:
        decision = ReuseDecision.ADAPT
        reason = "EXTERNAL_OR_NON_NATIVE_CANDIDATE_REQUIRES_ADAPTER"
    return SelectionResult(capability, decision, best.candidate_id, score, reason, ranked)
