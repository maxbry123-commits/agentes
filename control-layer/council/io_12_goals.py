"""Council · plantilla I/O de 12 goals · solo inv/diseño/plan/arquitectura.

LOW tasks → no council.
El host puede inyectar llm_panel; el núcleo trae veredicto determinista mínimo.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Callable, Mapping, Optional, Sequence


class CouncilPhase(str, Enum):
    INVESTIGACION = "investigacion"
    DISENO = "diseno"
    PLANIFICACION = "planificacion"
    ARQUITECTURA = "arquitectura"
    # fuera de alcance council por defecto:
    EJECUCION = "ejecucion"
    REVIEW = "review"


COUNCIL_PHASES = {
    CouncilPhase.INVESTIGACION,
    CouncilPhase.DISENO,
    CouncilPhase.PLANIFICACION,
    CouncilPhase.ARQUITECTURA,
}

# 12 goals de entrada/salida (simétricos)
GOAL_KEYS: tuple[str, ...] = (
    "g01_objetivo",
    "g02_alcance",
    "g03_restricciones",
    "g04_riesgos",
    "g05_alternativas",
    "g06_dependencias",
    "g07_contratos",
    "g08_evidencia",
    "g09_plan_pasos",
    "g10_criterios_done",
    "g11_no_hacer",
    "g12_siguiente",
)


@dataclass
class CouncilRequest:
    phase: CouncilPhase
    mission_id: str
    level: str  # LOW | MID | HIGH | EXTREME
    goals_in: dict[str, str]
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["phase"] = self.phase.value
        return d


@dataclass
class CouncilVerdict:
    phase: CouncilPhase
    approved: bool
    score: float  # 0-1
    goals_out: dict[str, str]
    risks: tuple[str, ...]
    missing: tuple[str, ...]
    notes: tuple[str, ...]
    used_llm: bool

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["phase"] = self.phase.value
        return d


def should_run_council(phase: CouncilPhase | str, level: str = "MID") -> bool:
    """LOW nunca; ejecucion/review no por defecto; diseño sí."""
    if str(level).upper() == "LOW":
        return False
    p = phase if isinstance(phase, CouncilPhase) else CouncilPhase(str(phase).lower())
    return p in COUNCIL_PHASES


def build_request(
    *,
    phase: CouncilPhase | str,
    mission_id: str,
    level: str = "MID",
    goals_in: Mapping[str, str] | None = None,
    context: Mapping[str, Any] | None = None,
) -> CouncilRequest:
    p = phase if isinstance(phase, CouncilPhase) else CouncilPhase(str(phase).lower())
    g = {k: "" for k in GOAL_KEYS}
    if goals_in:
        for k, v in goals_in.items():
            if k in g:
                g[k] = str(v)
    return CouncilRequest(
        phase=p,
        mission_id=mission_id,
        level=str(level).upper(),
        goals_in=g,
        context=dict(context or {}),
    )


def _deterministic_verdict(req: CouncilRequest) -> CouncilVerdict:
    """Sin LLM: aprueba si goals críticos no vacíos; lista missing."""
    missing = [k for k in ("g01_objetivo", "g02_alcance", "g09_plan_pasos", "g10_criterios_done") if not (req.goals_in.get(k) or "").strip()]
    risks: list[str] = []
    if not (req.goals_in.get("g04_riesgos") or "").strip():
        risks.append("riesgos_no_declarados")
    if not (req.goals_in.get("g11_no_hacer") or "").strip():
        risks.append("no_hacer_vacio")

    goals_out = dict(req.goals_in)
    if not goals_out.get("g12_siguiente"):
        goals_out["g12_siguiente"] = "completar_gaps" if missing else "continuar_fase"

    score = max(0.0, 1.0 - 0.15 * len(missing) - 0.1 * len(risks))
    approved = len(missing) == 0 and score >= 0.7

    return CouncilVerdict(
        phase=req.phase,
        approved=approved,
        score=round(score, 3),
        goals_out=goals_out,
        risks=tuple(risks),
        missing=tuple(missing),
        notes=("deterministic_panel",),
        used_llm=False,
    )


def run_council_deterministic(
    req: CouncilRequest,
    *,
    llm_panel: Optional[Callable[[CouncilRequest], CouncilVerdict]] = None,
) -> CouncilVerdict:
    """Si should_run_council es False → veredicto trivial approved.

    llm_panel opcional para HIGH/EXTREME; núcleo no depende de él.
    """
    if not should_run_council(req.phase, req.level):
        return CouncilVerdict(
            phase=req.phase,
            approved=True,
            score=1.0,
            goals_out=dict(req.goals_in),
            risks=(),
            missing=(),
            notes=("council_skipped_low_or_non_design",),
            used_llm=False,
        )

    if llm_panel is not None and req.level in ("HIGH", "EXTREME"):
        v = llm_panel(req)
        return v

    return _deterministic_verdict(req)
