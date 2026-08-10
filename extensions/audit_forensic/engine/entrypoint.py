# -*- coding: utf-8 -*-
"""Audit orchestrator — A-AUD-07. Packet → matrices → verdict. 0% LLM."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .doc_truth import DocumentTruthStore
from .matrix_contradiction import contradiction_summary, run_contradiction
from .matrix_coverage import coverage_summary, run_coverage
from .matrix_gaps import gaps_summary, run_gaps
from .matrix_literal import literal_summary, run_literal
from .packet_normalizer import PacketError, normalize_packet
from .repo_truth import FakeRepoTruth, GitHubRepoTruth, RepoTruthPort
from .requirements_loader import load_requirements
from .verdict_engine import decide_verdict

_ROOT = Path(__file__).resolve().parents[1]


def _default_repo_port(
    packet: dict[str, Any],
    repo_port: RepoTruthPort | None,
) -> RepoTruthPort:
    if repo_port is not None:
        return repo_port
    meta = packet.get("repo") or {}
    owner = meta.get("owner") or "maxbry123-commits"
    name = meta.get("name") or "agentes"
    return GitHubRepoTruth(owner, name)


def run_audit(
    raw_packet: dict[str, Any] | None,
    *,
    repo_port: RepoTruthPort | None = None,
    phase: str | None = None,
    deferred_ids: set[str] | None = None,
    doc_seed: Path | str | None = None,
    req_seed: Path | str | None = None,
) -> dict[str, Any]:
    deferred_ids = deferred_ids or set()

    try:
        packet = normalize_packet(raw_packet)
        packet_ok = True
        packet_flags = packet.get("flags") or {}
    except PacketError as e:
        return {
            "ok": False,
            "packet": None,
            "verdict": decide_verdict(
                coverage_summary={"counts": {}, "total": 0, "critical_missing": []},
                literal_summary={"counts": {}, "fails": [], "total": 0},
                contradiction_summary={
                    "total": 0,
                    "fails": [],
                    "fail_count": 0,
                    "has_critical_fail": False,
                },
                gaps_summary={
                    "total": 0,
                    "critical_count": 0,
                    "critical_ids": [],
                    "has_critical_gap": False,
                },
                packet_ok=False,
            ),
            "matrices": {},
            "error": {"reason_code": e.reason_code, "detail": e.detail},
        }

    doc_path = Path(doc_seed) if doc_seed else _ROOT / "store" / "document_truth_seed.yaml"
    req_path = Path(req_seed) if req_seed else _ROOT / "requirements" / "phase_seed.yaml"

    doc_store = DocumentTruthStore.from_seed(doc_path)
    requirements = load_requirements(req_path, phase=phase)
    port = _default_repo_port(packet, repo_port)

    cov_rows = run_coverage(requirements, packet, port, deferred_ids=deferred_ids)
    lit_rows = run_literal(requirements, packet, port, doc_store)
    con_rows = run_contradiction(packet, port)
    gap_rows = run_gaps(cov_rows, phase=phase, deferred_ids=deferred_ids)

    cov_s = coverage_summary(cov_rows)
    lit_s = literal_summary(lit_rows)
    con_s = contradiction_summary(con_rows)
    gap_s = gaps_summary(gap_rows)

    verdict = decide_verdict(
        coverage_summary=cov_s,
        literal_summary=lit_s,
        contradiction_summary=con_s,
        gaps_summary=gap_s,
        packet_flags=packet_flags,
        packet_ok=packet_ok,
    )

    return {
        "ok": True,
        "packet": {
            "task_id": packet.get("task_id"),
            "claim_status": packet.get("claim_status"),
            "final_commit": (packet.get("repo") or {}).get("final_commit"),
            "packet_hash": packet.get("packet_hash"),
        },
        "verdict": verdict,
        "matrices": {
            "coverage": cov_rows,
            "literal": lit_rows,
            "contradiction": con_rows,
            "gaps": gap_rows,
        },
        "summaries": {
            "coverage": cov_s,
            "literal": lit_s,
            "contradiction": con_s,
            "gaps": gap_s,
        },
    }


def run_audit_fake(
    raw_packet: dict[str, Any] | None,
    fake: FakeRepoTruth,
    **kwargs: Any,
) -> dict[str, Any]:
    return run_audit(raw_packet, repo_port=fake, **kwargs)
