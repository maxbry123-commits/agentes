"""Three offline simulations: UI + agents + Fake E2E.

Does not claim C100. Vendor LLM remains DENY.
"""
from __future__ import annotations

from typing import Any


def sim1_ui_ingest(text: str = "objective: wire ui to reception\nsuccess: ingest invoked") -> dict[str, Any]:
    """SIM-1: provisional UI → handle_message(ingest)."""
    try:
        from wordflow_kernel.ui_gateway import UIGatewayPlugin, UIMessage
    except ImportError:
        from extensions.wordflow_kernel.ui_gateway import UIGatewayPlugin, UIMessage

    plugin = UIGatewayPlugin(wire_kernel=True)
    resp = plugin.handle(UIMessage(session_id="sim1", text=text))
    return {
        "id": "SIM-1",
        "name": "ui_ingest",
        "ok": resp.status in ("ROUTED", "PARTIAL"),
        "status": resp.status,
        "ingest_ok": bool((resp.detail or {}).get("ingest_ok")),
        "health": plugin.health(),
        "llm_control": "DENY",
    }


def sim2_ui_agents(text: str = "reason a deterministic plan for reception ingest") -> dict[str, Any]:
    """SIM-2: UI → OpenClaw + Hermes stubs via Mock gateway."""
    try:
        from wordflow_kernel.gateway.intelligence import MockIntelligenceGateway
        from wordflow_kernel.engines import (
            EngineRegistry,
            EngineRequest,
            HermesEngine,
            OpenClawEngine,
        )
    except ImportError:
        from extensions.wordflow_kernel.gateway.intelligence import MockIntelligenceGateway
        from extensions.wordflow_kernel.engines import (
            EngineRegistry,
            EngineRequest,
            HermesEngine,
            OpenClawEngine,
        )

    gw = MockIntelligenceGateway(fixed_text="SIM2_STUB")
    reg = EngineRegistry()
    reg.register(OpenClawEngine())
    reg.register(HermesEngine())
    req = EngineRequest(
        task_id="sim2",
        trace_id="sim2-trace",
        messages=[{"role": "user", "content": text}],
        policy={"llm_control": "DENY"},
        context={"sim": 2},
    )
    results = {}
    for eid in ("openclaw", "hermes"):
        res = reg.reason(eid, req, gw)
        results[eid] = {"status": res.status, "content": res.content, "invoked": True}
    ok = all(v["invoked"] and v["status"] in ("STUB", "OK", "MOCK") for v in results.values())
    return {
        "id": "SIM-2",
        "name": "ui_agents",
        "ok": ok,
        "engines": results,
        "registered": reg.list_ids(),
        "llm_control": "DENY",
        "vendor_call": False,
    }


def sim3_ui_fake_e2e(goal: str = "objective: fake e2e from provisional ui\nsuccess: c19 invoked and blocked") -> dict[str, Any]:
    """SIM-3: UI session → bootstrap_fake. C-19 PASS is forbidden."""
    import tempfile
    from pathlib import Path

    try:
        from wordflow_kernel.bootstrap_fake import run_bootstrap_fake
        from wordflow_kernel.instance_store import InstanceStore, PersistentRegistry
        from wordflow_kernel.ui_gateway import UIGatewayPlugin, UIMessage
    except ImportError:
        from extensions.wordflow_kernel.bootstrap_fake import run_bootstrap_fake
        from extensions.wordflow_kernel.instance_store import InstanceStore, PersistentRegistry
        from extensions.wordflow_kernel.ui_gateway import UIGatewayPlugin, UIMessage

    ui = UIGatewayPlugin(wire_kernel=True).handle(UIMessage(session_id="sim3", text=goal))
    with tempfile.TemporaryDirectory() as tmp:
        store = InstanceStore(root=Path(tmp))
        reg = PersistentRegistry(store=store)
        out = run_bootstrap_fake("sim3", registry=reg, goal=goal)
    return {
        "id": "SIM-3",
        "name": "ui_fake_e2e",
        "ok": bool(out.get("ok")) and out.get("c19_pass") is False,
        "c19_pass": out.get("c19_pass"),
        "stages": out.get("stages"),
        "code_path_verdict": (out.get("code_path") or {}).get("verdict"),
        "ui_status": ui.status,
        "published": (out.get("deploy") or {}).get("published"),
        "llm_control": "DENY",
    }


def run_three() -> dict[str, Any]:
    sims = [sim1_ui_ingest(), sim2_ui_agents(), sim3_ui_fake_e2e()]
    return {
        "ok": all(s.get("ok") for s in sims),
        "sims": sims,
        "c100": False,
        "operational": "OFFLINE_STUB" if all(s.get("ok") for s in sims) else "FAIL",
        "note": "operativo offline: UI+stubs+Fake E2E. No vendor, no C100, no live ROUTER_URL.",
    }


if __name__ == "__main__":
    report = run_three()
    assert report["c100"] is False
    print("ok", report["operational"], [(s["id"], s["ok"]) for s in report["sims"]])
