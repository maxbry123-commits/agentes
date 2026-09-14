"""G28 Suficiencia (Confidence Engine) — ANTES de actuar.
SOURCE: SALIDA_6 · umbral 70 fijo.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Confidence:
    score: int
    ok: bool
    breakdown: dict[str, int]


def g28_suficiencia(
    research: int = 0,
    tests: int = 0,
    docs: int = 0,
    experience: int = 0,
    threshold: int = 70,
) -> Confidence:
    # pesos: Research 35 · Tests 25 · Docs 20 · Experiencia 20
    score = int(
        research * 0.35 + tests * 0.25 + docs * 0.20 + experience * 0.20
    )
    score = max(0, min(100, score))
    return Confidence(
        score=score,
        ok=score >= threshold,
        breakdown={
            "research": research,
            "tests": tests,
            "docs": docs,
            "experience": experience,
        },
    )
