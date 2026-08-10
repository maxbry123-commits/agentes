# -*- coding: utf-8 -*-
"""P0 Coverage matrix — A-AUD-04. requirement → path → status. 0% LLM."""
from __future__ import annotations

from typing import Any

from .repo_truth import RepoTruthPort

STATUS = frozenset(
    {"PRESENT", "MISSING", "STUB", "EXTRA", "NO_VERIFICADO", "DEFERRED"}
)


def _path_from_req(req: dict[str, Any]) -> str | None:
    if req.get("check_type") == "path_exists":
        return (req.get("params") or {}).get("path")
    if req.get("check_type") == "ci_success":
        return None
    return (req.get("params") or {}).get("path")


def run_coverage(
    requirements: list[dict[str, Any]],
    packet: dict[str, Any],
    repo: RepoTruthPort,
    *,
    deferred_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    deferred_ids = deferred_ids or set()
    ref = (packet.get("repo") or {}).get("final_commit") or ""
    claimed_paths = set()
    files = packet.get("files") or {}
    for key in ("added", "modified"):
        for p in files.get(key) or []:
            claimed_paths.add(p)

    rows: list[dict[str, Any]] = []
    req_paths: set[str] = set()

    for req in requirements:
        rid = req["id"]
        path = _path_from_req(req)
        critical = bool(req.get("critical"))
        phase = req.get("phase") or ""

        if rid in deferred_ids:
            rows.append(
                {
                    "requirement_id": rid,
                    "path_claim": path,
                    "path_real": False,
                    "status": "DEFERRED",
                    "critical": critical,
                    "phase": phase,
                }
            )
            continue

        if req.get("check_type") == "ci_success":
            tests = packet.get("tests") or {}
            has_ci = bool(tests.get("ci_run_id"))
            rows.append(
                {
                    "requirement_id": rid,
                    "path_claim": None,
                    "path_real": has_ci,
                    "status": "PRESENT" if has_ci else "NO_VERIFICADO",
                    "critical": critical,
                    "phase": phase,
                }
            )
            continue

        if not path:
            rows.append(
                {
                    "requirement_id": rid,
                    "path_claim": None,
                    "path_real": False,
                    "status": "NO_VERIFICADO",
                    "critical": critical,
                    "phase": phase,
                }
            )
            continue

        req_paths.add(path)
        exists = repo.path_exists(ref, path) if ref else False
        in_claim = path in claimed_paths

        if exists:
            status = "PRESENT"
        elif in_claim:
            status = "NO_VERIFICADO"
        else:
            status = "MISSING"

        rows.append(
            {
                "requirement_id": rid,
                "path_claim": path if in_claim else None,
                "path_real": exists,
                "status": status,
                "critical": critical,
                "phase": phase,
            }
        )

    for p in sorted(claimed_paths - req_paths):
        exists = repo.path_exists(ref, p) if ref else False
        rows.append(
            {
                "requirement_id": None,
                "path_claim": p,
                "path_real": exists,
                "status": "EXTRA",
                "critical": False,
                "phase": "",
            }
        )

    return rows


def coverage_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for r in rows:
        s = r["status"]
        counts[s] = counts.get(s, 0) + 1
    critical_missing = [
        r["requirement_id"]
        for r in rows
        if r.get("critical") and r["status"] in ("MISSING", "NO_VERIFICADO")
    ]
    return {
        "counts": counts,
        "total": len(rows),
        "critical_missing": critical_missing,
    }
