"""Tests A12 · council gates."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from council.io_12_goals import (
    CouncilPhase,
    build_request,
    run_council_deterministic,
    should_run_council,
)


def test_low_skips():
    assert should_run_council(CouncilPhase.DISENO, "LOW") is False
    req = build_request(phase="diseno", mission_id="m", level="LOW")
    v = run_council_deterministic(req)
    assert v.approved is True
    assert "skipped" in v.notes[0]


def test_ejecucion_skips():
    assert should_run_council(CouncilPhase.EJECUCION, "HIGH") is False


def test_arquitectura_requires_goals():
    req = build_request(phase="arquitectura", mission_id="m", level="HIGH", goals_in={})
    v = run_council_deterministic(req)
    assert v.approved is False
    assert "g01_objetivo" in v.missing


def test_complete_goals_approve():
    goals = {
        "g01_objetivo": "API pagos",
        "g02_alcance": "v1",
        "g09_plan_pasos": "1,2,3",
        "g10_criterios_done": "tests verdes",
        "g04_riesgos": "PCI",
        "g11_no_hacer": "no crypto propia",
    }
    req = build_request(phase="planificacion", mission_id="m", level="MID", goals_in=goals)
    v = run_council_deterministic(req)
    assert v.approved is True
    assert v.used_llm is False


if __name__ == "__main__":
    test_low_skips()
    test_ejecucion_skips()
    test_arquitectura_requires_goals()
    test_complete_goals_approve()
    print("A12 tests OK")
