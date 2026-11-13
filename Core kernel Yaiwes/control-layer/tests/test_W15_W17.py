"""W15-W17 tests."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from contracts.failure import Failure, FailureType
from contracts.output_contract import compile_output, validate_output
from wordflow.control_bus import ControlBus


def test_output_contract():
    oc, v = compile_output(
        goal="auth",
        result="implemented",
        evidence={"tests": "green"},
        limitations=["no oauth"],
        termination="complete",
        next_state={"done": True},
    )
    assert v.ok is True
    bad = validate_output({"goal": "x"})
    assert bad.ok is False


def test_control_bus_happy_path():
    with tempfile.TemporaryDirectory() as td:
        bus = ControlBus(td)
        goals_in = {
            "G01_objetivo": "auth",
            "G02_alcance": "backend",
            "G03_restricciones": "none",
            "G05_recursos": "1h",
            "G09_criterio_done": "tests",
            "G10_no_hacer": "no secrets",
        }
        start = bus.start_mission(workflow_id="w1", goals_in=goals_in, estimated_tokens=1000)
        assert start["ok"] is True
        bus.remember(project_id="P1", agent_id="coder", content="decidimos JWT")
        goals_out = {
            "O01_objetivo_cumplido": "auth done",
            "O05_seguridad": "ok",
            "O09_evidencia": "tests",
            "O10_aprobacion_final": "yes",
        }
        end = bus.finish_mission(
            workflow_id="w1",
            goals_out=goals_out,
            result="done",
            evidence={"hash": "abc"},
        )
        assert end["ok"] is True


def test_control_bus_preview_block():
    with tempfile.TemporaryDirectory() as td:
        bus = ControlBus(td)
        goals_in = {
            "G01_objetivo": "huge",
            "G02_alcance": "all",
            "G03_restricciones": "x",
            "G05_recursos": "x",
            "G09_criterio_done": "x",
            "G10_no_hacer": "x",
        }
        start = bus.start_mission(
            workflow_id="w2",
            goals_in=goals_in,
            estimated_tokens=200_000,
            user_confirmed=False,
        )
        assert start["ok"] is False
        assert start["stage"] == "preview"


if __name__ == "__main__":
    test_output_contract()
    test_control_bus_happy_path()
    test_control_bus_preview_block()
    print("W15-W17 OK")
