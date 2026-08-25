# -*- coding: utf-8 -*-
"""Process 06 — Evidence packet + merge + path gateway."""
from __future__ import annotations

from typing import Any


def consult_path_gateway(mission_id: str, raw_input: str) -> dict[str, Any]:
    """CONN.path_gateway: runner → RouterHTTPGateway. Fail closed by default."""
    try:
        from extensions.wordflow_kernel.gateway.intelligence import make_request
        from extensions.wordflow_kernel.gateway.router_http import RouterHTTPGateway
    except ImportError:
        try:
            from wordflow_kernel.gateway.intelligence import make_request  # type: ignore
            from wordflow_kernel.gateway.router_http import RouterHTTPGateway  # type: ignore
        except ImportError:
            return {
                "ok": False,
                "invoked": False,
                "error": "GATEWAY_MISSING",
                "contract": "GAP",
                "llm_control": "DENY",
                "vendor_call": False,
            }

    gw = RouterHTTPGateway(allow_mock_fallback=False)
    req = make_request(
        task_id="C-19",
        capability="llm.complete",
        payload={
            "prompt": (raw_input or "")[:200],
            "mission_id": mission_id,
            "llm_control": "DENY",
        },
        policy={"max_cost": 0.0, "vendor": "DENY"},
    )
    res = gw.execute(req)
    return {
        "ok": res.status == "DENY" or bool(res.output),
        "invoked": True,
        "status": res.status,
        "provider": res.provider,
        "llm_control": "DENY",
        "contract": "WIRED_DENY",
        "vendor_call": False,
        "evidence_hash": res.evidence_hash,
        "reason": res.output.get("reason") if isinstance(res.output, dict) else None,
    }


def run_evidence(
    *,
    mission_id: str,
    raw_input: str,
    compiled: Any,
    consult_gateway: bool,
    wire_trace: dict[str, Any],
) -> dict[str, Any]:
    from extensions.wordflow.engine.evidence_packet import build_evidence_packet, verify_evidence_packet
    from extensions.wordflow.standards.evidence_merge import merge_evidence

    if consult_gateway:
        gw_hop = consult_path_gateway(mission_id, raw_input)
        wire_trace["path_gateway"] = gw_hop
    else:
        gw_hop = {"ok": False, "invoked": False, "contract": "SKIP"}
        wire_trace["path_gateway"] = gw_hop

    evidence = build_evidence_packet(
        task_id="C-19",
        claim_status="PARTIAL",
        paths=[{"path": "extensions/wordflow/engine/programming/runner.py"}],
        tests={
            "cognitive_ok": True,
            "skill_compiled": compiled is not None,
            "path_gateway": bool(gw_hop.get("invoked")),
        },
        doc_anchors=["C-19", "FORENSIC_ENFORCEMENT"],
        notes=f"mission={mission_id}",
    )
    evidence_ok = verify_evidence_packet(evidence)["ok"]
    merged = merge_evidence(
        engine_packet=evidence if isinstance(evidence, dict) else None,
        mission_id=mission_id or "mission-local",
        task_id="C-19",
    )
    wire_trace["evidence_merge"] = {"complete": merged.get("complete")}
    return {
        "evidence": evidence,
        "evidence_ok": evidence_ok,
        "merged": merged,
        "path_gateway": gw_hop,
    }
