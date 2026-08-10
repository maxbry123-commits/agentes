# -*- coding: utf-8 -*-
"""Fetch planner — A-SE-02. Pin → deterministic download plan. 0% LLM."""
from __future__ import annotations

from typing import Any, Protocol

from .version_pin import VersionPinError, normalize_pin


class FetcherPort(Protocol):
    def plan(self, pin: dict[str, Any]) -> dict[str, Any]: ...
    def execute(self, plan: dict[str, Any]) -> dict[str, Any]: ...


def build_fetch_plan(raw_pin: dict[str, Any] | None) -> dict[str, Any]:
    pin = normalize_pin(raw_pin)
    st = pin["source_type"]
    loc = pin["locator"]
    digest = pin["digest"]

    steps: list[dict[str, Any]] = []
    if st == "git":
        steps = [
            {"op": "git_clone", "uri": loc["uri"], "ref": loc.get("ref") or "HEAD"},
            {"op": "git_checkout", "ref": loc.get("ref") or digest["value"]},
            {"op": "verify_commit", "expected": digest["value"]},
        ]
        if loc.get("path"):
            steps.append({"op": "sparse_checkout", "path": loc["path"]})
    elif st == "hf":
        steps = [
            {"op": "hf_download", "uri": loc["uri"], "revision": loc.get("ref")},
            {"op": "verify_sha256", "expected": digest["value"]},
        ]
    elif st == "release":
        steps = [
            {"op": "http_get", "uri": loc["uri"]},
            {"op": "verify_sha256", "expected": digest["value"]},
            {"op": "extract_archive"},
        ]
    elif st == "package":
        steps = [
            {
                "op": "package_download",
                "name": loc.get("package_name") or loc["uri"],
                "version": loc.get("version"),
            },
            {"op": "verify_sha256", "expected": digest["value"]},
        ]
    elif st == "url":
        steps = [
            {"op": "http_get", "uri": loc["uri"]},
            {"op": "verify_sha256", "expected": digest["value"]},
        ]
    elif st == "local":
        steps = [
            {"op": "local_copy", "uri": loc["uri"]},
            {"op": "verify_sha256", "expected": digest["value"]},
        ]
    else:
        raise VersionPinError("UNSUPPORTED_SOURCE", st)

    return {
        "plan_id": f"plan-{pin['pin_id']}",
        "pin_id": pin["pin_id"],
        "pin_hash": pin["pin_hash"],
        "source_type": st,
        "llm_control": pin.get("llm_control", "DENY"),
        "steps": steps,
        "status": "PLANNED",
        "artifact_dir": f"artifacts/sources/{pin['pin_id']}",
    }


class FakeFetcher:
    def __init__(self, *, fail_on: str | None = None):
        self.fail_on = fail_on
        self.executed: list[dict[str, Any]] = []

    def plan(self, pin: dict[str, Any]) -> dict[str, Any]:
        return build_fetch_plan(pin)

    def execute(self, plan: dict[str, Any]) -> dict[str, Any]:
        results = []
        for step in plan.get("steps") or []:
            op = step.get("op")
            if self.fail_on and op == self.fail_on:
                results.append({"op": op, "status": "FAILED", "reason": "simulated"})
                return {
                    "plan_id": plan.get("plan_id"),
                    "status": "FAILED",
                    "steps": results,
                    "artifact_dir": plan.get("artifact_dir"),
                }
            results.append({"op": op, "status": "OK"})
        self.executed.append(plan)
        return {
            "plan_id": plan.get("plan_id"),
            "status": "SUCCESS",
            "steps": results,
            "artifact_dir": plan.get("artifact_dir"),
            "pin_id": plan.get("pin_id"),
        }
