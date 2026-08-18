"""Catálogo de puntos de programación (subset accionable) — dataset para checklist obligatoria.
No implementa 500 gates: define referentes que el agente DEBE declarar y el sheriff VERIFICA.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set

@dataclass(frozen=True)
class ProgPoint:
    id: str
    stage: str  # context|plan|copy|apply|verify|verdict
    title: str
    required_default: bool = False

# Referentes de programación (alto ROI / aplicables al path code) — no compliance teatro
PROGRAMMING_POINTS: List[ProgPoint] = [
    ProgPoint("E451", "context", "context_verified must be proven", True),
    ProgPoint("E452", "context", "handoff_verified must be proven", True),
    ProgPoint("E001", "context", "@file scope if multi-file", False),
    ProgPoint("E003", "context", "@git diff in context", False),
    ProgPoint("E012", "context", "secrets redaction", True),
    ProgPoint("E051", "plan", "plan before multi-file", True),
    ProgPoint("E056", "plan", "blast radius estimate", True),
    ProgPoint("E082", "plan", "path allowlist in plan", True),
    ProgPoint("E087", "plan", "COPY vs ADAPT vs GENERATE explicit", True),
    ProgPoint("E088", "plan", "COPY sources listed if ADAPT/COPY", True),
    ProgPoint("E101", "apply", "path allowlist writes", True),
    ProgPoint("E103", "apply", "max files per apply", True),
    ProgPoint("E104", "apply", "max LOC delta", False),
    ProgPoint("E121", "apply", "paired test touch if module change", True),
    ProgPoint("E147", "apply", "SOURCE→DEST evidence on copy", True),
    ProgPoint("E151", "verify", "typecheck gate if stack supports", False),
    ProgPoint("E152", "verify", "lint gate if stack supports", False),
    ProgPoint("E154", "verify", "affected tests", True),
    ProgPoint("E157", "verify", "import cycle check", True),
    ProgPoint("E160", "verify", "secret scan", True),
    ProgPoint("E198", "verify", "skip != pass", True),
    ProgPoint("E199", "verify", "required gate missing = fail", True),
    ProgPoint("E200", "verify", "evidence packet after gates", True),
    ProgPoint("E234", "verdict", "hallucinated path detect", True),
    ProgPoint("E235", "verdict", "hallucinated symbol detect", True),
    ProgPoint("E236", "verdict", "invented import detect", True),
    ProgPoint("E247", "verdict", "human gate if high risk", False),
    ProgPoint("E453", "verify", "scope from git diff", True),
    ProgPoint("E455", "verdict", "no core=True without measure", True),
    ProgPoint("E489", "apply", "SOURCE→DEST required if ADAPT", True),
    ProgPoint("E490", "copy", "regenerate blocked if hash match", True),
    ProgPoint("E492", "context", "prompt injection scan raw_input", False),
]

BY_ID: Dict[str, ProgPoint] = {p.id: p for p in PROGRAMMING_POINTS}

def required_ids_for_stages(stages: Set[str] | None = None) -> List[str]:
    stages = stages or {"context", "plan", "copy", "apply", "verify", "verdict"}
    return [p.id for p in PROGRAMMING_POINTS if p.required_default and p.stage in stages]

def all_ids() -> List[str]:
    return [p.id for p in PROGRAMMING_POINTS]
