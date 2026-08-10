# -*- coding: utf-8 -*-
"""P2 Contradiction matrix — A-AUD-05. Claim vs repo truth. 0% LLM."""
from __future__ import annotations

from typing import Any

from .repo_truth import RepoTruthPort


def run_contradiction(
    packet: dict[str, Any],
    repo: RepoTruthPort,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    repo_meta = packet.get("repo") or {}
    ref = repo_meta.get("final_commit") or ""
    files = packet.get("files") or {}
    loc = packet.get("loc_claim") or {}
    tests = packet.get("tests") or {}

    commit = repo.get_commit(ref) if ref else None
    if not ref:
        rows.append({
            "pair": "final_commit",
            "status": "FAIL",
            "reason_code": "INVALID_COMMIT_SHA",
            "detail": "empty final_commit",
        })
    elif commit is None:
        rows.append({
            "pair": "final_commit",
            "status": "NO_VERIFICADO",
            "reason_code": "REPO_TRUTH_UNAVAILABLE",
            "detail": ref,
        })
    else:
        rows.append({
            "pair": "final_commit",
            "status": "PASS",
            "reason_code": None,
            "sha": commit.get("sha"),
        })

    claimed_added = list(files.get("added") or [])
    missing_in_tree = []
    if ref:
        for p in claimed_added:
            if not repo.path_exists(ref, p):
                missing_in_tree.append(p)
    if claimed_added and missing_in_tree:
        rows.append({
            "pair": "files_added_vs_tree",
            "status": "FAIL",
            "reason_code": "PATH_NOT_IN_REPO",
            "missing": missing_in_tree,
        })
    elif claimed_added:
        rows.append({
            "pair": "files_added_vs_tree",
            "status": "PASS",
            "reason_code": None,
            "count": len(claimed_added),
        })
    else:
        rows.append({
            "pair": "files_added_vs_tree",
            "status": "NO_VERIFICADO",
            "reason_code": None,
            "detail": "no files.added",
        })

    if loc and commit and commit.get("stats"):
        stats = commit["stats"]
        mismatches = []
        for key in ("additions", "deletions"):
            if key in loc and stats.get(key) is not None:
                if int(loc[key]) != int(stats[key]):
                    mismatches.append({"field": key, "claim": loc[key], "real": stats[key]})
        if "net" in loc and stats.get("additions") is not None and stats.get("deletions") is not None:
            real_net = int(stats["additions"]) - int(stats["deletions"])
            if int(loc["net"]) != real_net:
                mismatches.append({"field": "net", "claim": loc["net"], "real": real_net})
        rows.append({
            "pair": "loc_vs_stats",
            "status": "FAIL" if mismatches else "PASS",
            "reason_code": "LOC_CLAIM_MISMATCH" if mismatches else None,
            "mismatches": mismatches,
        })
    elif loc:
        rows.append({
            "pair": "loc_vs_stats",
            "status": "NO_VERIFICADO",
            "reason_code": "REPO_TRUTH_UNAVAILABLE",
        })

    claimed_passed = int(tests.get("claimed_passed") or 0)
    run_id = tests.get("ci_run_id")
    if claimed_passed > 0:
        if not run_id:
            rows.append({
                "pair": "tests_vs_ci",
                "status": "FAIL",
                "reason_code": "CI_MISSING",
            })
        else:
            run = repo.get_workflow_run(str(run_id))
            if not run:
                rows.append({
                    "pair": "tests_vs_ci",
                    "status": "NO_VERIFICADO",
                    "reason_code": "REPO_TRUTH_UNAVAILABLE",
                })
            else:
                ok = run.get("conclusion") == "success"
                head = run.get("head_sha")
                head_ok = (not ref) or (not head) or head == ref or str(head).startswith(ref[:7])
                reason = None
                if not ok:
                    reason = "CI_FAILED"
                elif not head_ok:
                    reason = "CI_HEAD_MISMATCH"
                rows.append({
                    "pair": "tests_vs_ci",
                    "status": "PASS" if ok and head_ok else "FAIL",
                    "reason_code": reason,
                    "conclusion": run.get("conclusion"),
                    "head_sha": head,
                })
    else:
        rows.append({
            "pair": "tests_vs_ci",
            "status": "PASS",
            "reason_code": None,
            "detail": "no tests claimed",
        })

    return rows


def contradiction_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    fails = [r for r in rows if r["status"] == "FAIL"]
    return {
        "total": len(rows),
        "fails": fails,
        "fail_count": len(fails),
        "has_critical_fail": len(fails) > 0,
    }
