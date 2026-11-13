# -*- coding: utf-8 -*-
"""Council of 12 — A-WF-05. Deterministic votes. 0% LLM."""
from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


def _roles_path() -> Path:
    return Path(__file__).resolve().parents[1] / "store" / "council_roles.yaml"


def load_roles(path: Path | str | None = None) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML required")
    p = Path(path) if path else _roles_path()
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return {
        "roles": list(data.get("roles") or []),
        "quorum": int(data.get("quorum") or 7),
        "rules": dict(data.get("rules") or {}),
    }


def _vote_role(
    role: dict[str, Any],
    *,
    sentinel: dict[str, Any] | None,
    refute: dict[str, Any] | None,
    block: dict[str, Any] | None,
) -> dict[str, Any]:
    rid = role["id"]
    name = role["name"]
    sentinel = sentinel or {}
    refute = refute or {}
    block = block or {}
    flags = block.get("flags") or {}
    constraints = block.get("constraints") or {}

    approve = True
    reason = "ok"

    if name == "Architect":
        if not block.get("raw_text"):
            approve, reason = False, "no objective text"
    elif name == "Security":
        if flags.get("rejected") or "SECRET" in str(refute.get("codes") or []):
            approve, reason = False, "security reject"
    elif name == "Determinism":
        if block.get("quality_bar") == "draft":
            approve, reason = False, "draft not deterministic path"
    elif name == "QualityBar":
        if sentinel.get("verdict") == "FAIL":
            approve, reason = False, "sentinel FAIL"
        if block.get("quality_bar") == "never_MVP" and not constraints.get("success_criteria"):
            approve, reason = False, "never_MVP without criteria"
    elif name == "Schema":
        if sentinel and any(
            c.get("name") == "schema" and c.get("status") == "FAIL"
            for c in sentinel.get("checks") or []
        ):
            approve, reason = False, "schema fail"
    elif name == "Tests":
        if constraints.get("tests_required") and not constraints.get("tests_planned"):
            approve, reason = False, "tests required not planned"
    elif name == "LOC_Budget":
        loc = constraints.get("loc_limit")
        if loc is not None and int(loc) > 300:
            approve, reason = False, f"loc={loc}>300"
    elif name == "Traceability":
        if not (block.get("doc_refs") or block.get("goals_hint")):
            approve, reason = False, "no anchors/hints"
    elif name == "Recovery":
        if refute.get("worst_layer") == "L1" and not refute.get("pass"):
            approve, reason = False, "L1 structural"
    elif name == "Deploy":
        if constraints.get("deploy") and not constraints.get("deploy_plan"):
            approve, reason = False, "deploy without plan"
    elif name == "Evidence":
        if block.get("quality_bar") == "never_MVP" and not constraints.get("success_criteria"):
            approve, reason = False, "no success criteria for evidence"
    elif name == "DirectorProxy":
        if flags.get("rejected"):
            approve, reason = False, "block rejected"

    return {
        "role_id": rid,
        "name": name,
        "vote": "APPROVE" if approve else "REJECT",
        "veto": bool(role.get("veto")) and not approve,
        "weight": int(role.get("weight") or 1),
        "reason": reason,
    }


def run_council(
    *,
    block: dict[str, Any] | None = None,
    sentinel: dict[str, Any] | None = None,
    refute: dict[str, Any] | None = None,
    roles_path: Path | str | None = None,
) -> dict[str, Any]:
    cfg = load_roles(roles_path)
    votes = [
        _vote_role(r, sentinel=sentinel, refute=refute, block=block)
        for r in cfg["roles"]
    ]
    approves = [v for v in votes if v["vote"] == "APPROVE"]
    rejects = [v for v in votes if v["vote"] == "REJECT"]
    vetos = [v for v in votes if v.get("veto")]

    weight_approve = sum(v["weight"] for v in approves)
    weight_reject = sum(v["weight"] for v in rejects)

    rules = cfg["rules"]
    if rules.get("any_veto_reject") and vetos:
        decision = "REJECT"
    elif len(approves) >= cfg["quorum"] and weight_approve > weight_reject:
        decision = "APPROVE"
    elif rules.get("fail_closed"):
        decision = "REJECT"
    else:
        decision = "APPROVE" if weight_approve >= weight_reject else "REJECT"

    return {
        "decision": decision,
        "votes": votes,
        "approve_count": len(approves),
        "reject_count": len(rejects),
        "veto_count": len(vetos),
        "vetos": [{"role": v["name"], "reason": v["reason"]} for v in vetos],
        "quorum": cfg["quorum"],
        "weight_approve": weight_approve,
        "weight_reject": weight_reject,
    }
