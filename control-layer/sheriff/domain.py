"""W11 · Domain Sheriffs encima del Sheriff 5 · 0% LLM."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping


class Domain(str, Enum):
    INPUT = "input"
    RESEARCH = "research"
    CODE = "code"
    GITHUB = "github"
    FINAL = "final"


@dataclass
class DomainVerdict:
    domain: Domain
    allow: bool
    reasons: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["domain"] = self.domain.value
        return d


def sheriff_input(payload: Mapping[str, Any] | None) -> DomainVerdict:
    data = dict(payload or {})
    reasons: list[str] = []
    if not str(data.get("goal") or data.get("G01_objetivo") or "").strip():
        reasons.append("missing_goal")
    if data.get("critical") and not data.get("confirm_critical"):
        reasons.append("critical_unconfirmed")
    return DomainVerdict(Domain.INPUT, allow=len(reasons) == 0, reasons=reasons)


def sheriff_research(payload: Mapping[str, Any] | None) -> DomainVerdict:
    data = dict(payload or {})
    reasons: list[str] = []
    n = int(data.get("candidates_count") or 0)
    min_n = int(data.get("min_candidates") or 20)
    if n < min_n and not data.get("skip_min_research"):
        reasons.append(f"research_below_min:{n}<{min_n}")
    if not data.get("licenses_ok", True):
        reasons.append("license_block")
    return DomainVerdict(Domain.RESEARCH, allow=len(reasons) == 0, reasons=reasons, evidence={"n": n})


def sheriff_code(payload: Mapping[str, Any] | None) -> DomainVerdict:
    data = dict(payload or {})
    reasons: list[str] = []
    if data.get("from_scratch") and not data.get("source_mirror_id"):
        reasons.append("from_scratch_without_mirror")
    if data.get("secrets_detected"):
        reasons.append("secrets_in_code")
    return DomainVerdict(Domain.CODE, allow=len(reasons) == 0, reasons=reasons)


def sheriff_github(payload: Mapping[str, Any] | None) -> DomainVerdict:
    data = dict(payload or {})
    reasons: list[str] = []
    if data.get("agent_has_token"):
        reasons.append("agent_must_not_hold_token")
    if not data.get("repo_bound"):
        reasons.append("repo_not_bound")
    if data.get("force_push"):
        reasons.append("force_push_denied")
    return DomainVerdict(Domain.GITHUB, allow=len(reasons) == 0, reasons=reasons)


def sheriff_final(payload: Mapping[str, Any] | None) -> DomainVerdict:
    data = dict(payload or {})
    reasons: list[str] = []
    for k in ("O01_objetivo_cumplido", "O09_evidencia", "O10_aprobacion_final"):
        if not str(data.get(k) or "").strip():
            reasons.append(f"missing_{k}")
    if data.get("unresolved_critical"):
        reasons.append("unresolved_critical")
    return DomainVerdict(Domain.FINAL, allow=len(reasons) == 0, reasons=reasons)


DOMAIN_SHERIFFS = {
    Domain.INPUT: sheriff_input,
    Domain.RESEARCH: sheriff_research,
    Domain.CODE: sheriff_code,
    Domain.GITHUB: sheriff_github,
    Domain.FINAL: sheriff_final,
}


def run_domain(domain: Domain | str, payload: Mapping[str, Any] | None = None) -> DomainVerdict:
    d = domain if isinstance(domain, Domain) else Domain(str(domain))
    return DOMAIN_SHERIFFS[d](payload)
