# -*- coding: utf-8 -*-
"""main_12 loop runner — A-WF-06 + W2 evidence bridge. Deterministic. 0% LLM."""
from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

from .council import run_council
from .evidence_bridge import goals_out_to_evidence_packet
from .goals_extractor import empty_goals_out, extract_goals_in
from .input_normalizer import InputBlockError, normalize_input_block
from .refute_repair import apply_auto_repairs, propose_repairs, refute_block
from .sentinel import run_sentinel


def _loop_path() -> Path:
    return Path(__file__).resolve().parents[1] / "store" / "main_12.yaml"


def load_main_12(path: Path | str | None = None) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML required")
    p = Path(path) if path else _loop_path()
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return {
        "loop_id": data.get("loop_id", "main_12"),
        "steps": list(data.get("steps") or []),
        "on_fail": data.get("on_fail", "stop"),
        "on_reject": data.get("on_reject", "stop"),
    }


def _build_task_list(block: dict[str, Any], goals_in: dict[str, Any]) -> list[dict[str, Any]]:
    hints = block.get("goals_hint") or []
    paths = (goals_in.get("resolved") or {}).get("GIN-08", {}).get("value") or []
    tasks = []
    for i, h in enumerate(hints):
        tasks.append({
            "id": f"T{i+1:02d}",
            "title": str(h),
            "status": "PENDING",
            "priority": block.get("priority", "P1"),
        })
    for i, p in enumerate(paths):
        tasks.append({
            "id": f"F{i+1:02d}",
            "title": f"materialize {p}",
            "path": p,
            "status": "PENDING",
            "priority": block.get("priority", "P1"),
        })
    if not tasks:
        tasks.append({
            "id": "T01",
            "title": (block.get("raw_text") or "")[:80],
            "status": "PENDING",
            "priority": block.get("priority", "P1"),
        })
    return tasks


def run_main_12(
    raw: dict[str, Any] | None,
    *,
    loop_path: Path | str | None = None,
    repo: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = load_main_12(loop_path)
    state: dict[str, Any] = {
        "loop_id": cfg["loop_id"],
        "step_results": [],
        "status": "RUNNING",
        "block": None,
        "goals_in": None,
        "refute": None,
        "repairs": [],
        "sentinel": None,
        "council": None,
        "tasks": [],
        "goals_out": empty_goals_out(),
        "evidence_packet": None,
        "stop_reason": None,
    }

    def _record(step_id: str, name: str, ok: bool, detail: Any = None):
        state["step_results"].append(
            {"id": step_id, "name": name, "ok": ok, "detail": detail}
        )

    try:
        block = normalize_input_block(raw)
        state["block"] = block
        _record("S01", "normalize_input", True, block.get("block_hash"))
    except InputBlockError as e:
        _record("S01", "normalize_input", False, e.reason_code)
        state["status"] = "FAILED"
        state["stop_reason"] = e.reason_code
        return state

    goals_in = extract_goals_in(block)
    state["goals_in"] = goals_in
    state["goals_out"]["GOUT-01"] = {
        "name": "normalized_block", "value": block.get("block_hash"), "status": "DONE",
    }
    state["goals_out"]["GOUT-02"] = {
        "name": "goals_in_resolved", "value": goals_in.get("covered_ids"), "status": "DONE",
    }
    _record("S02", "extract_goals_in", True, goals_in.get("covered_count"))

    refute = refute_block(block, goals_in)
    state["refute"] = refute
    state["goals_out"]["GOUT-05"] = {
        "name": "refute_report", "value": refute.get("codes"), "status": "DONE",
    }
    _record("S03", "refute", refute["pass"], refute.get("codes"))

    proposals = propose_repairs(refute, block)
    block2, applied = apply_auto_repairs(block, proposals)
    state["block"] = block2
    state["repairs"] = {"proposals": proposals, "applied": applied}
    state["goals_out"]["GOUT-06"] = {
        "name": "repair_actions", "value": applied, "status": "DONE",
    }
    _record("S04", "repair", True, applied)

    raw2 = {
        "schema_version": block2.get("schema_version", "1.0"),
        "block_id": block2.get("block_id"),
        "source_type": block2.get("source_type"),
        "raw_text": block2.get("raw_text"),
        "quality_bar": block2.get("quality_bar"),
        "goals_hint": block2.get("goals_hint"),
        "priority": block2.get("priority"),
        "doc_refs": block2.get("doc_refs"),
        "constraints": block2.get("constraints"),
        "meta": block2.get("meta"),
        "parent_block_id": block2.get("parent_block_id"),
    }
    goals_in2 = extract_goals_in(block2)
    sentinel = run_sentinel(raw2, goals_in=goals_in2)
    state["sentinel"] = sentinel
    state["goals_out"]["GOUT-07"] = {
        "name": "sentinel_verdict", "value": sentinel.get("verdict"), "status": "DONE",
    }
    _record("S05", "sentinel", sentinel["verdict"] == "PASS", sentinel.get("reason_codes"))
    if sentinel["verdict"] != "PASS":
        state["status"] = "FAILED"
        state["stop_reason"] = "SENTINEL_FAIL"
        if cfg["on_fail"] == "stop":
            return state

    council = run_council(block=block2, sentinel=sentinel, refute=refute)
    state["council"] = council
    state["goals_out"]["GOUT-08"] = {
        "name": "council_vote", "value": council.get("decision"), "status": "DONE",
    }
    _record("S06", "council", council["decision"] == "APPROVE", council.get("decision"))
    if council["decision"] != "APPROVE":
        state["status"] = "REJECTED"
        state["stop_reason"] = "COUNCIL_REJECT"
        if cfg["on_reject"] == "stop":
            return state

    tasks = _build_task_list(block2, goals_in2)
    state["tasks"] = tasks
    state["goals_out"]["GOUT-03"] = {
        "name": "task_list", "value": [t["id"] for t in tasks], "status": "DONE",
    }
    _record("S07", "build_task_list", True, len(tasks))

    plan = {
        "next": tasks[0]["id"] if tasks else None,
        "total": len(tasks),
        "priority": block2.get("priority"),
    }
    state["goals_out"]["GOUT-04"] = {
        "name": "plan_cursor", "value": plan, "status": "DONE",
    }
    _record("S08", "plan_cursor", True, plan)

    _record("S09", "emit_goals_out", True, sum(
        1 for g in state["goals_out"].values() if g.get("status") == "DONE"
    ))

    # W2: formal EvidencePacket (replaces 4-field stub)
    packet = goals_out_to_evidence_packet(
        block=block2,
        goals_out=state["goals_out"],
        tasks=tasks,
        loop_status="RUNNING",
        repo=repo,
    )
    state["evidence_packet"] = packet
    state["goals_out"]["GOUT-10"] = {
        "name": "evidence_packet", "value": packet.get("task_id"), "status": "DONE",
    }
    _record("S10", "build_evidence_packet", True, packet.get("claim_status"))

    state["checkpoint"] = {
        "block_hash": block2.get("block_hash"),
        "steps_ok": sum(1 for s in state["step_results"] if s["ok"]),
        "steps_total": len(state["step_results"]),
    }
    _record("S11", "checkpoint", True, state["checkpoint"])

    state["goals_out"]["GOUT-12"] = {
        "name": "next_block_hint", "value": plan.get("next"), "status": "DONE",
    }
    _record("S12", "next_or_stop", True, plan.get("next"))
    state["status"] = "COMPLETED"
    # refresh claim_status mapping after COMPLETED (still PARTIAL until W9)
    state["evidence_packet"] = goals_out_to_evidence_packet(
        block=block2,
        goals_out=state["goals_out"],
        tasks=tasks,
        loop_status="COMPLETED",
        repo=repo,
    )
    return state
