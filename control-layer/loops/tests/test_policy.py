"""Policy engine tests · 0% LLM"""
from loops.contracts.types import DetectorResult
from loops.policy.engine import PolicyEngine, PolicyInput


def test_stall_repair():
    eng = PolicyEngine([
        {
            "id": "stall_repair",
            "when": {"detectors": ["stall"], "min_severity": 0.5, "min_iteration": 2},
            "action": "REPAIR",
            "reason": "stall",
        }
    ])
    d = DetectorResult(detector="stall", severity=0.8, fired_at="t", run_id="R1")
    dec = eng.evaluate(PolicyInput(run_id="R1", iteration=3, detectors=[d]))
    assert dec.action == "REPAIR"
    assert dec.policy_rule_id == "stall_repair"


def test_default_continue():
    eng = PolicyEngine([])
    dec = eng.evaluate(PolicyInput(run_id="R1"))
    assert dec.action == "CONTINUE"


def test_validation_escalate_on_repair_exhausted():
    eng = PolicyEngine([
        {
            "id": "esc",
            "when": {"phase_outcome": "validation_failed", "min_repair": 2},
            "action": "ESCALATE",
            "reason": "done",
        }
    ])
    dec = eng.evaluate(PolicyInput(run_id="R1", phase_outcome="validation_failed", repair_count=2))
    assert dec.action == "ESCALATE"
