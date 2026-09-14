from loops.phases import PhaseResult
from loops.progress_from_phases import extract_progress_signal, progress_from_phases


def test_extract_tests():
    pr = [PhaseResult(phase="ejecutar", ok=True, output={"tests": {"passed": 8, "total": 10}})]
    kind, val = extract_progress_signal(pr)
    assert kind == "tests" and val["passed"] == 8
    p = progress_from_phases(pr)
    assert abs(p.progress_score - 0.8) < 0.01


def test_extract_validation():
    pr = [
        PhaseResult(phase="ejecutar", ok=True, output={"agent_output": {"x": 1}}),
        PhaseResult(phase="validar", ok=True, output={"validation": {"has_output": True}}),
    ]
    kind, val = extract_progress_signal(pr)
    assert kind == "validation" and val is True
