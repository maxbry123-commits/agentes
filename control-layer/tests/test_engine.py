from control.engine import run_engine


def test_read_local_green():
    r = run_engine({"text": "read config file", "action": "read"})
    assert r["sheriff"]["state"] in {"GREEN", "YELLOW"}
    assert "C03" in r["plan"]["contracts"] or len(r["plan"]["contracts"]) >= 1


def test_secret_write_not_naive():
    r = run_engine({"text": "install with token credential", "action": "install", "data_sensitivity": "secret"})
    assert r["plan"]["threat_score"] >= 5
