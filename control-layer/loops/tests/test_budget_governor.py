from loops.budget_governor import BudgetGovernor, budget_from_level


def test_charge_and_exhaust():
    g = BudgetGovernor(budget_from_level("micro"))
    # micro tokens 20000
    r = g.charge(tokens=20000, run_id="R1")
    assert not r.ok
    assert "tokens" in r.exhausted
    assert any(d.detector == "budget" for d in r.detectors)


def test_warning_80():
    g = BudgetGovernor(budget_from_level("micro"))
    r = g.charge(tokens=16000, run_id="R1")  # 80% of 20k
    assert r.ok
    assert "tokens" in r.warnings


def test_reallocate():
    a = BudgetGovernor(budget_from_level("micro"))
    b = BudgetGovernor(budget_from_level("micro"))
    a.charge(tokens=1000)
    moved = b.reallocate_from(a, 0.5)
    assert moved.get("tokens", 0) > 0
