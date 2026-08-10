# -*- coding: utf-8 -*-
"""P1 Literalidad matrix — A-AUD-04. Doc/requirement checks. 0% LLM."""
from __future__ import annotations

from typing import Any

from .doc_truth import DocumentTruthStore
from .repo_truth import RepoTruthPort


def run_literal(
    requirements: list[dict[str, Any]],
    packet: dict[str, Any],
    repo: RepoTruthPort,
    doc_store: DocumentTruthStore,
) -> list[dict[str, Any]]:
    ref = (packet.get("repo") or {}).get("final_commit") or ""
    blob_shas = packet.get("blob_shas") or {}
    tests = packet.get("tests") or {}
    rows: list[dict[str, Any]] = []

    for anchor in packet.get("doc_anchors") or []:
        resolved = doc_store.resolve_anchor(anchor)
        rows.append(
            {
                "check": "doc_anchor",
                "target": anchor.get("doc_id"),
                "section": anchor.get("section"),
                "status": "PASS" if resolved.get("ok") else "FAIL",
                "reason_code": resolved.get("reason_code"),
                "detail": resolved,
            }
        )

    for req in requirements:
        rid = req["id"]
        ctype = req.get("check_type")
        params = req.get("params") or {}

        if ctype == "path_exists":
            path = params.get("path")
            if not path or not ref:
                rows.append(
                    {
                        "check": "path_exists",
                        "target": rid,
                        "status": "NO_VERIFICADO",
                        "reason_code": "PATH_NOT_IN_REPO",
                    }
                )
                continue
            ok = repo.path_exists(ref, path)
            rows.append(
                {
                    "check": "path_exists",
                    "target": rid,
                    "path": path,
                    "status": "PASS" if ok else "FAIL",
                    "reason_code": None if ok else "PATH_NOT_IN_REPO",
                }
            )
            if path in blob_shas:
                claimed = blob_shas[path]
                real = repo.get_blob_sha(ref, path)
                match = real is not None and real == claimed
                rows.append(
                    {
                        "check": "blob_sha",
                        "target": rid,
                        "path": path,
                        "status": "PASS" if match else "FAIL",
                        "reason_code": None if match else "BLOB_SHA_MISMATCH",
                        "claimed": claimed,
                        "real": real,
                    }
                )

        elif ctype == "ci_success":
            run_id = tests.get("ci_run_id")
            claimed_passed = int(tests.get("claimed_passed") or 0)
            if claimed_passed > 0 and not run_id:
                rows.append(
                    {
                        "check": "ci_success",
                        "target": rid,
                        "status": "FAIL",
                        "reason_code": "CI_MISSING",
                    }
                )
                continue
            if not run_id:
                rows.append(
                    {
                        "check": "ci_success",
                        "target": rid,
                        "status": "NO_VERIFICADO",
                        "reason_code": "CI_MISSING",
                    }
                )
                continue
            run = repo.get_workflow_run(str(run_id))
            if not run:
                rows.append(
                    {
                        "check": "ci_success",
                        "target": rid,
                        "status": "NO_VERIFICADO",
                        "reason_code": "REPO_TRUTH_UNAVAILABLE",
                    }
                )
                continue
            ok = run.get("conclusion") == "success"
            head_ok = True
            if ref and run.get("head_sha"):
                head_ok = str(run["head_sha"]).startswith(ref[:7]) or run["head_sha"] == ref
            rows.append(
                {
                    "check": "ci_success",
                    "target": rid,
                    "status": "PASS" if ok and head_ok else "FAIL",
                    "reason_code": (
                        None
                        if ok and head_ok
                        else ("CI_FAILED" if not ok else "CI_HEAD_MISMATCH")
                    ),
                    "conclusion": run.get("conclusion"),
                    "head_sha": run.get("head_sha"),
                }
            )
        else:
            rows.append(
                {
                    "check": ctype or "custom",
                    "target": rid,
                    "status": "NO_VERIFICADO",
                    "reason_code": "NO_VERIFICADO",
                }
            )

    return rows


def literal_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    fails = []
    for r in rows:
        s = r["status"]
        counts[s] = counts.get(s, 0) + 1
        if s == "FAIL":
            fails.append({"target": r.get("target"), "reason_code": r.get("reason_code")})
    return {"counts": counts, "total": len(rows), "fails": fails}
