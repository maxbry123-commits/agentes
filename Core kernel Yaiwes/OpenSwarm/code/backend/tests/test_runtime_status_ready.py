"""ENG-190: the status payload distinguishes 'spawned' from 'serving' and names the one address a
client can open, instead of running=True with an unactionable port."""

from backend.apps.outputs.runtime import AppRuntime


def p_rt(tmp_path, new_mode: bool) -> AppRuntime:
    ws = tmp_path / "ws"
    ws.mkdir(exist_ok=True)
    if new_mode:
        (ws / "run.sh").write_text("#!/bin/bash\n")
    rt = AppRuntime(workspace_id="ws-test", workspace_path=str(ws))
    return rt


def test_ready_false_while_spawned_but_not_serving(tmp_path, monkeypatch):
    rt = p_rt(tmp_path, new_mode=True)
    monkeypatch.setattr(type(rt), "running", property(lambda self: True))
    rt.frontend_port = 5173
    rt.p_frontend_ready = False
    assert rt.ready is False
    assert rt.frontend_url is None


def test_ready_true_once_port_answers_and_falls_with_process(tmp_path, monkeypatch):
    rt = p_rt(tmp_path, new_mode=True)
    monkeypatch.setattr(type(rt), "running", property(lambda self: True))
    rt.frontend_port = 5173
    rt.p_frontend_ready = True
    assert rt.ready is True
    assert rt.frontend_url == "http://127.0.0.1:5173/"
    monkeypatch.setattr(type(rt), "running", property(lambda self: False))
    assert rt.ready is False
    assert rt.frontend_url is None


def test_frozen_runtime_is_not_ready(tmp_path, monkeypatch):
    rt = p_rt(tmp_path, new_mode=True)
    monkeypatch.setattr(type(rt), "running", property(lambda self: True))
    rt.frontend_port = 5173
    rt.p_frontend_ready = True
    rt.p_suspended = True
    assert rt.ready is False


def test_status_payload_carries_ready_and_serving_url(tmp_path, monkeypatch):
    from backend.apps.outputs import outputs as outputs_mod
    from backend.apps.outputs.runtime import manager

    rt = p_rt(tmp_path, new_mode=True)
    monkeypatch.setattr(type(rt), "running", property(lambda self: True))
    rt.frontend_port = 5173
    rt.p_frontend_ready = True
    monkeypatch.setitem(manager.runtimes, "ws-test", rt)
    payload = outputs_mod.runtime_status_payload("ws-test")
    assert payload["ready"] is True
    assert payload["serving_url"] == "http://127.0.0.1:5173/"
    rt.p_frontend_ready = False
    payload = outputs_mod.runtime_status_payload("ws-test")
    assert payload["running"] is True and payload["ready"] is False and payload["serving_url"] is None
