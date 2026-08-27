import importlib


def test_p01_to_p12_cable(monkeypatch):
    mod = importlib.import_module("Refactoria.G5.new.pipeline_p01_p12")

    def fake_runner(raw_input, **kwargs):
        return {"ok": True, "verdict": "PASS", "wire_trace": {"closure_engine": {"closed": True}}}

    runner = importlib.import_module("extensions.wordflow.engine.code_path_runner")
    monkeypatch.setattr(runner, "run_code_path", fake_runner)

    out = mod.execute_p01_p12("deterministic wordflow integration input")
    assert out["ok"] is True
    assert out["cable"] == "p01→p02→p03→p04→p05→p06→p07→p08→p09→p10→p11→p12"
    assert [x["p"] for x in out["p_trace"]] == [f"p{i:02d}" for i in range(1, 13)]
    assert all(x["ok"] for x in out["p_trace"][:11])


def test_p01_guard_fail_closed():
    mod = importlib.import_module("Refactoria.G5.new.pipeline_p01_p12")
    out = mod.execute_p01_p12("")
    assert out["ok"] is False
    assert out["stage"] == "context"
