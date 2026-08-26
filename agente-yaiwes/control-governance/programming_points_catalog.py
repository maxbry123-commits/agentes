"""Catálogo rediseñado: CORE | CONDITIONAL | ADVISORY | REFERENCE.
No 500 gates. Metadatos ejecutables + applicability tags.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Set, Optional

@dataclass(frozen=True)
class ProgPoint:
    id: str
    stage: str
    title: str
    enforcement: str  # CORE | CONDITIONAL | ADVISORY | REFERENCE
    applicability: frozenset  # tags: always, multi_file, external_api, db, concurrency, ai_agent, ui, new_dep, security, public_api, side_effects
    evidence_type: str  # path|symbol|test|measure|commit|manifest

def _p(id: str, stage: str, title: str, enforcement: str, apps: Set[str], evidence_type: str) -> ProgPoint:
    return ProgPoint(id, stage, title, enforcement, frozenset(apps), evidence_type)

PROGRAMMING_POINTS: List[ProgPoint] = [
    # CORE — siempre en tareas de programming code
    _p("C-CTX-01", "context", "ContextManifest complete", "CORE", {"always"}, "manifest"),
    _p("C-CTX-02", "context", "Handoff verified with artifact", "CORE", {"always"}, "manifest"),
    _p("C-CTX-03", "context", "No secrets in context", "CORE", {"always"}, "measure"),
    _p("C-PLN-01", "plan", "Action COPY|ADAPT|GENERATE explicit", "CORE", {"always"}, "measure"),
    _p("C-PLN-02", "plan", "Scope paths declared", "CORE", {"always"}, "path"),
    _p("C-CPY-01", "copy", "COPY-FIRST scan executed", "CORE", {"always"}, "measure"),
    _p("C-CPY-02", "copy", "GENERATE only if no match", "CORE", {"always"}, "measure"),
    _p("C-CPY-03", "copy", "SOURCE→DEST if COPY/ADAPT", "CORE", {"always"}, "path"),
    _p("C-APL-01", "apply", "Path allowlist respected", "CORE", {"always"}, "path"),
    _p("C-VRF-01", "verify", "Evidence packet present", "CORE", {"always"}, "measure"),
    _p("C-VRF-02", "verify", "SKIP != PASS", "CORE", {"always"}, "measure"),
    _p("C-VRF-03", "verify", "Required gate missing = FAIL", "CORE", {"always"}, "measure"),
    _p("C-WRD-01", "verdict", "VerdictAuthority only", "CORE", {"always"}, "measure"),
    _p("C-WRD-02", "verdict", "Agent claim is not verification", "CORE", {"always"}, "measure"),
    _p("C-GAP-01", "verdict", "new_gaps_after_fix == 0", "CORE", {"always"}, "measure"),
    # CONDITIONAL
    _p("K-MUL-01", "plan", "Plan before multi-file", "CONDITIONAL", {"multi_file"}, "manifest"),
    _p("K-MUL-02", "apply", "Max files / blast radius", "CONDITIONAL", {"multi_file"}, "measure"),
    _p("K-TST-01", "verify", "Affected tests run", "CONDITIONAL", {"always"}, "test"),
    _p("K-TST-02", "verify", "Paired test if module changed", "CONDITIONAL", {"multi_file"}, "test"),
    _p("K-DEP-01", "verify", "New dependency justified", "CONDITIONAL", {"new_dep"}, "path"),
    _p("K-API-01", "verify", "Public API consumer or not public", "CONDITIONAL", {"public_api"}, "symbol"),
    _p("K-SEC-01", "verify", "Secret scan clean", "CONDITIONAL", {"security"}, "measure"),
    _p("K-CON-01", "verify", "Concurrency notes/tests", "CONDITIONAL", {"concurrency"}, "test"),
    _p("K-SFX-01", "verify", "Idempotency if side effects", "CONDITIONAL", {"side_effects"}, "test"),
    _p("K-DB-01", "verify", "Migration dry-run", "CONDITIONAL", {"db"}, "path"),
    _p("K-EXT-01", "verify", "External API contract", "CONDITIONAL", {"external_api"}, "path"),
    _p("K-AI-01", "verify", "Agent tool allowlist", "CONDITIONAL", {"ai_agent"}, "manifest"),
    # ADVISORY (no bloquean solos)
    _p("A-IMP-01", "verify", "Impact fan-out noted", "ADVISORY", {"multi_file"}, "measure"),
    _p("A-CYC-01", "verify", "Import cycle check", "ADVISORY", {"always"}, "measure"),
    _p("A-LOC-01", "apply", "LOC soft budget", "ADVISORY", {"always"}, "measure"),
    # REFERENCE patterns (no enforcement)
    _p("R-HEX-01", "plan", "Prefer port/adapter over core edit", "REFERENCE", {"always"}, "manifest"),
    _p("R-CPY-01", "copy", "Prefer COPY/ADAPT over GENERATE", "REFERENCE", {"always"}, "manifest"),
]

BY_ID: Dict[str, ProgPoint] = {p.id: p for p in PROGRAMMING_POINTS}
CATALOG_VERSION = "2.0.0"

def core_ids() -> List[str]:
    return [p.id for p in PROGRAMMING_POINTS if p.enforcement == "CORE"]

def points_for_tags(tags: Set[str]) -> List[ProgPoint]:
    out = []
    for p in PROGRAMMING_POINTS:
        if p.enforcement == "CORE":
            out.append(p)
        elif p.enforcement == "CONDITIONAL" and (p.applicability & tags):
            out.append(p)
        elif p.enforcement == "ADVISORY" and (p.applicability & tags or "always" in p.applicability):
            out.append(p)
    return out
