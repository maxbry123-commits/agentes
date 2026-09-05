from loops.risk import RiskEngine, HumanGate


def test_high_delete():
    r = RiskEngine().assess(["delete"])
    assert r.level == "high"
    assert r.require_human
    g = HumanGate().decide(r)
    assert g.pause and g.mode == "HUMAN_APPROVAL"


def test_low_read():
    r = RiskEngine().assess(["read", "search"])
    assert r.level == "low"
    g = HumanGate().decide(r)
    assert g.allow and g.mode == "AUTO"


def test_production_flag():
    r = RiskEngine().assess(["write_code"], context_flags={"production": True})
    assert r.level == "high"
