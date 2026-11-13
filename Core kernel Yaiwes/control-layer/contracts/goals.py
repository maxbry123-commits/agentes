"""W02 · Goals 10-in / 10-out · validación determinista."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

GOALS_IN_REQUIRED = (
    "G01_objetivo",
    "G02_alcance",
    "G03_restricciones",
    "G05_recursos",
    "G09_criterio_done",
    "G10_no_hacer",
)

GOALS_OUT_REQUIRED = (
    "O01_objetivo_cumplido",
    "O05_seguridad",
    "O09_evidencia",
    "O10_aprobacion_final",
)


@dataclass
class GoalsValidation:
    ok: bool
    missing: list[str] = field(default_factory=list)
    filled: list[str] = field(default_factory=list)
    score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_goals_in(payload: Mapping[str, Any] | None) -> GoalsValidation:
    data = dict(payload or {})
    missing = [g for g in GOALS_IN_REQUIRED if not str(data.get(g) or "").strip()]
    filled = [g for g in GOALS_IN_REQUIRED if g not in missing]
    score = len(filled) / max(1, len(GOALS_IN_REQUIRED))
    return GoalsValidation(ok=len(missing) == 0, missing=missing, filled=filled, score=score)


def validate_goals_out(payload: Mapping[str, Any] | None) -> GoalsValidation:
    data = dict(payload or {})
    missing = [g for g in GOALS_OUT_REQUIRED if not str(data.get(g) or "").strip()]
    filled = [g for g in GOALS_OUT_REQUIRED if g not in missing]
    score = len(filled) / max(1, len(GOALS_OUT_REQUIRED))
    return GoalsValidation(ok=len(missing) == 0, missing=missing, filled=filled, score=score)
