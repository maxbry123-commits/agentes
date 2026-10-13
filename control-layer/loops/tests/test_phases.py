"""9-phase + Sheriff tests · 0% LLM"""
from loops.phases import PhaseRunner, PhaseResult, PhaseSpec, Sheriff, PHASE_ORDER, REQUIRED


def test_order_and_required():
    assert len(PHASE_ORDER) == 9
    assert "ejecutar" in REQUIRED
    assert "plan" not in REQUIRED


def test_sheriff_blocks_missing_required():
    sh = Sheriff()
    results = [PhaseResult(phase="plan", ok=True)]  # missing required
    v = sh.check(results)
    assert not v.ok
    assert "leer_anclas" in v.missing_required


def test_runner_default_all_ok():
    runner = PhaseRunner()
    results, verdict = runner.run({})
    assert len(results) == 9
    assert verdict.ok


def test_runner_stops_on_required_fail():
    def fail_exec(_ctx):
        return PhaseResult(phase="ejecutar", ok=False, error="boom")

    runner = PhaseRunner(handlers={"ejecutar": fail_exec})
    results, verdict = runner.run({})
    assert not verdict.ok
    assert "ejecutar" in verdict.failed_required
    # phases after ejecutar may not all run
    ids = [r.phase for r in results]
    assert "ejecutar" in ids
