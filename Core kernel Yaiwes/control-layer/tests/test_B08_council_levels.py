"""B08 · sim S6/S7 · LOW sin Council · EXTREME arquitectura con Council."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from council.io_12_goals import (
    CouncilPhase,
    build_request,
    run_council_deterministic,
    should_run_council,
)


def test_s6_low_never_runs_council():
    for phase in (
        CouncilPhase.INVESTIGACION,
        CouncilPhase.DISENO,
        CouncilPhase.PLANIFICACION,
        CouncilPhase.ARQUITECTURA,
    ):
        assert should_run_council(phase, "LOW") is False
        req = build_request(phase=phase, mission_id="m", level="LOW")
        v = run_council_deterministic(req)
        assert v.approved is True
        assert v.used_llm is False
        assert any("skipped" in n for n in v.notes)


def test_ejecucion_never_even_if_extreme():
    assert should_run_council(CouncilPhase.EJECUCION, "EXTREME") is False


def test_s7_extreme_arquitectura_runs_and_can_reject():
    assert should_run_council(CouncilPhase.ARQUITECTURA, "EXTREME") is True
    req = build_request(
        phase="arquitectura",
        mission_id="m",
        level="EXTREME",
        goals_in={},  # incompleto
    )
    v = run_council_deterministic(req)
    assert v.used_llm is False  # núcleo determinista
    assert v.approved is False
    assert len(v.missing) > 0


def test_s7_extreme_complete_goals_approve():
    goals = {
        "g01_objetivo": "pagos PCI",
        "g02_alcance": "v1 charge",
        "g04_riesgos": "PCI-DSS",
        "g09_plan_pasos": "1 design 2 impl 3 audit",
        "g10_criterios_done": "pen-test ok",
        "g11_no_hacer": "no store CVV",
    }
    req = build_request(
        phase="arquitectura",
        mission_id="m",
        level="EXTREME",
        goals_in=goals,
    )
    v = run_council_deterministic(req)
    assert v.approved is True
    assert v.score >= 0.7


if __name__ == "__main__":
    test_s6_low_never_runs_council()
    test_ejecucion_never_even_if_extreme()
    test_s7_extreme_arquitectura_runs_and_can_reject()
    test_s7_extreme_complete_goals_approve()
    print("B08 OK")
