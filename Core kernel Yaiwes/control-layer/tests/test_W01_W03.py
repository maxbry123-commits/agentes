"""W01-W03 tests."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from contracts.failure import Failure, FailureType, RecoveryStrategy, choose_recovery
from contracts.goals import validate_goals_in, validate_goals_out


def test_goals_in_missing():
    v = validate_goals_in({"G01_objetivo": "auth"})
    assert v.ok is False
    assert "G02_alcance" in v.missing


def test_goals_in_ok():
    payload = {
        "G01_objetivo": "auth",
        "G02_alcance": "backend",
        "G03_restricciones": "no oauth externo",
        "G05_recursos": "2h",
        "G09_criterio_done": "tests green",
        "G10_no_hacer": "no secrets en repo",
    }
    v = validate_goals_in(payload)
    assert v.ok is True
    assert v.score == 1.0


def test_goals_out_required():
    v = validate_goals_out({"O01_objetivo_cumplido": "yes"})
    assert v.ok is False


def test_failure_recovery_budget():
    f = Failure(type=FailureType.API_BUDGET, detail="quota", retryable=True)
    assert choose_recovery(f) == RecoveryStrategy.WAIT


def test_failure_max_retries_agent():
    f = Failure(type=FailureType.AGENT, detail="crash", retryable=True)
    assert choose_recovery(f, retries_done=3) == RecoveryStrategy.FALLBACK_AGENT


if __name__ == "__main__":
    test_goals_in_missing()
    test_goals_in_ok()
    test_goals_out_required()
    test_failure_recovery_budget()
    test_failure_max_retries_agent()
    print("W01-W03 OK")
