"""The apps SDK host surface (ENG-202): provider-agnostic LLM completions and positioned agent
spawns for OpenSwarm-built apps, plus the template helpers that ride them."""

import os

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)
P_TEMPLATE = os.path.join(os.path.dirname(__file__), "..", "apps", "outputs", "webapp_template")


def p_auth() -> dict:
    from backend.auth import init_auth_token
    return {"Authorization": f"Bearer {init_auth_token()}"}


class Blk:
    def __init__(self, type: str, text: str = "") -> None:
        self.type = type
        self.text = text


class FakeStream:
    def __init__(self, resp) -> None:
        self.resp = resp

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def get_final_message(self):
        return self.resp


class FakeLLMClient:
    def __init__(self) -> None:
        self.calls = []
        self.messages = self

    def stream(self, **kw):
        self.calls.append(kw)
        resp = type("R", (), {"content": [Blk("text", "hello from fake")]})()
        return FakeStream(resp)


def test_llm_routes_through_the_users_provider(monkeypatch):
    import backend.apps.agents.providers.registry as reg
    import backend.apps.settings.credentials as cred
    import backend.apps.settings.settings as settings_mod

    fake = FakeLLMClient()
    monkeypatch.setattr(settings_mod, "load_settings", lambda: {"fake": True}, raising=True)

    async def p_aux(settings, preferred_tier="haiku", primary_api=None):
        return ("aux-cheap", None)
    monkeypatch.setattr(reg, "resolve_aux_model", p_aux, raising=True)
    monkeypatch.setattr(cred, "get_anthropic_client_for_model", lambda s, m: fake, raising=True)

    r = client.post("/api/apps-sdk/llm", json={"prompt": "say hello"}, headers=p_auth())
    assert r.status_code == 200, r.text
    assert r.json() == {"text": "hello from fake", "model": "aux-cheap"}
    assert fake.calls[0]["model"] == "aux-cheap"


def test_llm_honors_an_explicit_model(monkeypatch):
    import backend.apps.agents.providers.registry as reg
    import backend.apps.settings.credentials as cred
    import backend.apps.settings.settings as settings_mod

    fake = FakeLLMClient()
    monkeypatch.setattr(settings_mod, "load_settings", lambda: {"fake": True}, raising=True)
    monkeypatch.setattr(reg, "resolve_model_id_for_sdk", lambda short, s: f"resolved-{short}", raising=True)
    monkeypatch.setattr(cred, "get_anthropic_client_for_model", lambda s, m: fake, raising=True)

    r = client.post("/api/apps-sdk/llm", json={"prompt": "hi", "model": "haiku", "system": "terse"},
                    headers=p_auth())
    assert r.status_code == 200, r.text
    assert r.json()["model"] == "resolved-haiku"
    assert fake.calls[0]["system"] == "terse"


def test_llm_rejects_an_empty_prompt():
    r = client.post("/api/apps-sdk/llm", json={"prompt": "   "}, headers=p_auth())
    assert r.status_code == 422


def test_spawn_agent_launches_and_broadcasts_position(monkeypatch):
    import backend.apps.dashboards.dashboards as dash_mod
    from backend.apps.agents import agent_manager as am_mod
    from backend.apps.agents.core import ws_manager as ws_mod
    from backend.apps.agents.core.models import AgentSession

    monkeypatch.setattr(dash_mod, "load_all", lambda: [], raising=True)
    launched = []
    messaged = []
    broadcasts = []

    async def p_launch(config):
        launched.append(config)
        return AgentSession(id="sess-1", name=config.name, model=config.model, mode=config.mode)

    async def p_send(session_id, prompt):
        messaged.append((session_id, prompt))

    async def p_broadcast(event, payload):
        broadcasts.append((event, payload))

    monkeypatch.setattr(am_mod.agent_manager, "launch_agent", p_launch, raising=True)
    monkeypatch.setattr(am_mod.agent_manager, "send_message", p_send, raising=True)
    monkeypatch.setattr(ws_mod.ws_manager, "broadcast_global", p_broadcast, raising=True)

    r = client.post("/api/apps-sdk/agents/spawn", json={
        "prompt": "research crm tools", "name": "CRM scout", "x": 400, "y": 300,
    }, headers=p_auth())
    assert r.status_code == 200, r.text
    assert r.json() == {"session_id": "sess-1"}
    assert launched[0].name == "CRM scout" and launched[0].prompt == "research crm tools"
    assert broadcasts == [("apps_sdk:place_agent_card",
                           {"session_id": "sess-1", "dashboard_id": None, "x": 400.0, "y": 300.0})]


def test_spawn_agent_without_position_skips_the_broadcast(monkeypatch):
    import backend.apps.dashboards.dashboards as dash_mod
    from backend.apps.agents import agent_manager as am_mod
    from backend.apps.agents.core import ws_manager as ws_mod
    from backend.apps.agents.core.models import AgentSession

    monkeypatch.setattr(dash_mod, "load_all", lambda: [], raising=True)
    broadcasts = []

    async def p_launch(config):
        return AgentSession(id="sess-2", name=config.name, model=config.model, mode=config.mode)

    async def p_send(session_id, prompt):
        return None

    async def p_broadcast(event, payload):
        broadcasts.append(event)

    monkeypatch.setattr(am_mod.agent_manager, "launch_agent", p_launch, raising=True)
    monkeypatch.setattr(am_mod.agent_manager, "send_message", p_send, raising=True)
    monkeypatch.setattr(ws_mod.ws_manager, "broadcast_global", p_broadcast, raising=True)

    r = client.post("/api/apps-sdk/agents/spawn", json={"prompt": "hi"}, headers=p_auth())
    assert r.status_code == 200
    assert broadcasts == []


def test_template_ships_both_sdk_helpers_and_the_skill_references_them():
    front = os.path.join(P_TEMPLATE, "frontend", "src", "openswarmHost.ts")
    back = os.path.join(P_TEMPLATE, "backend", "apps", "openswarm_host", "openswarm_host.py")
    guide = os.path.join(P_TEMPLATE, "SDK.md")
    assert os.path.exists(front) and os.path.exists(back) and os.path.exists(guide)
    skill_path = os.path.join(P_TEMPLATE, "..", "app_builder_skill.md")
    with open(skill_path, "r", encoding="utf-8") as f:
        skill = f.read()
    assert "SDK.md" in skill and "openswarmHost" in skill and "openswarm_host" in skill
    # The tools surface is wired behind per-app grants; the guide must teach the deny contract, not hide the gate.
    with open(guide, "r", encoding="utf-8") as f:
        text = f.read()
    assert "per-app" in text and "Allow once" in text and "never retry" in text


def p_isolated_grants(tmp_path, monkeypatch):
    from backend.apps.apps_sdk import app_identity, tool_grants
    monkeypatch.setattr(tool_grants, "GRANTS_FILE", str(tmp_path / "grants.json"))
    monkeypatch.setattr(app_identity, "APP_TOKENS_FILE", str(tmp_path / "app_tokens.json"))
    return tool_grants


def p_token_for(app: str) -> str:
    from backend.apps.apps_sdk.app_identity import mint_app_token
    return mint_app_token(app)


def test_tool_call_denied_grant_is_refused_flat(tmp_path, monkeypatch):
    grants = p_isolated_grants(tmp_path, monkeypatch)
    grants.set_grant("app1", "srv1:SendEmail", "denied")
    r = client.post("/api/apps-sdk/tools/call", headers=p_auth(),
                    json={"app_token": p_token_for("app1"), "tool": "srv1:SendEmail", "args": {}})
    assert r.status_code == 403
    assert "denied" in r.json()["detail"]


def test_tool_call_ungranted_times_out_to_deny(tmp_path, monkeypatch):
    from backend.apps.apps_sdk import tool_grants
    p_isolated_grants(tmp_path, monkeypatch)
    monkeypatch.setattr(tool_grants, "GRANT_WAIT_SECONDS", 0.05)
    called = {"n": 0}

    async def p_never(*a, **k):
        called["n"] += 1
        return "should not run"
    import backend.apps.tools_lib.mcp_call as mcp_call
    monkeypatch.setattr(mcp_call, "call_mcp_tool", p_never)
    r = client.post("/api/apps-sdk/tools/call", headers=p_auth(),
                    json={"app_token": p_token_for("app1"), "tool": "srv1:SendEmail", "args": {}})
    assert r.status_code == 403
    assert called["n"] == 0


def test_tool_call_granted_dispatches(tmp_path, monkeypatch):
    grants = p_isolated_grants(tmp_path, monkeypatch)
    grants.set_grant("app1", "srv1:SendEmail", "granted")

    async def p_fake_call(tool_id, tool_name, arguments):
        assert (tool_id, tool_name) == ("srv1", "SendEmail")
        return "sent: " + arguments["to"]
    import backend.apps.tools_lib.mcp_call as mcp_call
    monkeypatch.setattr(mcp_call, "call_mcp_tool", p_fake_call)
    r = client.post("/api/apps-sdk/tools/call", headers=p_auth(),
                    json={"app_token": p_token_for("app1"), "tool": "srv1:SendEmail", "args": {"to": "a@b.c"}})
    assert r.status_code == 200
    assert r.json()["result"] == "sent: a@b.c"


def test_grant_prompt_approval_flow_allows_and_remembers(tmp_path, monkeypatch):
    import asyncio
    grants = p_isolated_grants(tmp_path, monkeypatch)

    async def p_fake_call(tool_id, tool_name, arguments):
        return "ok"
    import backend.apps.tools_lib.mcp_call as mcp_call
    monkeypatch.setattr(mcp_call, "call_mcp_tool", p_fake_call)

    captured = {}

    async def p_capture_broadcast(event, payload):
        captured.update(payload)
        asyncio.get_running_loop().call_soon(
            lambda: grants.resolve_grant(payload["request_id"], True, True))
    from backend.apps.agents.core import ws_manager as wsm
    monkeypatch.setattr(wsm.ws_manager, "broadcast_global", p_capture_broadcast)
    r = client.post("/api/apps-sdk/tools/call", headers=p_auth(),
                    json={"app_token": p_token_for("app2"), "tool": "srv9:ReadSheet", "args": {}})
    assert r.status_code == 200
    assert captured["tool_label"] == "ReadSheet"
    assert grants.grant_status("app2", "srv9:ReadSheet") == "granted"


def test_tools_grant_route_unknown_request_is_no_op():
    r = client.post("/api/apps-sdk/tools/grant", headers=p_auth(),
                    json={"request_id": "nope", "allow": True})
    assert r.status_code == 200 and r.json()["ok"] is False


def test_bare_output_id_is_never_identity(tmp_path, monkeypatch):
    grants = p_isolated_grants(tmp_path, monkeypatch)
    grants.set_grant("app1", "srv1:SendEmail", "granted")
    # A caller who only KNOWS app1's id (no minted token, no Origin) must not inherit its grants.
    r = client.post("/api/apps-sdk/tools/call", headers=p_auth(),
                    json={"output_id": "app1", "tool": "srv1:SendEmail", "args": {}})
    assert r.status_code == 403
    assert "identify" in r.json()["detail"]


def test_token_for_app_a_cannot_use_app_bs_grants(tmp_path, monkeypatch):
    grants = p_isolated_grants(tmp_path, monkeypatch)
    grants.set_grant("app-b", "srv1:SendEmail", "granted")
    from backend.apps.apps_sdk import tool_grants
    monkeypatch.setattr(tool_grants, "GRANT_WAIT_SECONDS", 0.05)
    called = {"n": 0}

    async def p_never(*a, **k):
        called["n"] += 1
    import backend.apps.tools_lib.mcp_call as mcp_call
    monkeypatch.setattr(mcp_call, "call_mcp_tool", p_never)
    # app-a's token resolves to app-a, whose grant is absent, so the ask times out to deny.
    r = client.post("/api/apps-sdk/tools/call", headers=p_auth(),
                    json={"app_token": p_token_for("app-a"), "output_id": "app-b", "tool": "srv1:SendEmail", "args": {}})
    assert r.status_code == 403
    assert called["n"] == 0


def test_mint_is_stable_and_resolves(tmp_path, monkeypatch):
    p_isolated_grants(tmp_path, monkeypatch)
    from backend.apps.apps_sdk.app_identity import mint_app_token, resolve_app_token, revoke_app_token
    t1 = mint_app_token("app-x")
    t2 = mint_app_token("app-x")
    assert t1 == t2 and resolve_app_token(t1) == "app-x"
    assert resolve_app_token("forged-token") is None
    revoke_app_token("app-x")
    assert resolve_app_token(t1) is None
