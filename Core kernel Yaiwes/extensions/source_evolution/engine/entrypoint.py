# -*- coding: utf-8 -*-
"""Source evolution entrypoint — A-SE-04. 0% LLM."""
from __future__ import annotations

from typing import Any

from .fetch_planner import FakeFetcher, FetcherPort, build_fetch_plan
from .install_planner import build_install_plan
from .registry import SourceRegistry
from .version_pin import VersionPinError, normalize_pin


def run_acquire(
    raw_pin: dict[str, Any] | None,
    *,
    fetcher: FetcherPort | None = None,
    registry: SourceRegistry | None = None,
    execute: bool = True,
    target_dir: str = "vendor",
) -> dict[str, Any]:
    try:
        pin = normalize_pin(raw_pin)
    except VersionPinError as e:
        return {
            "ok": False,
            "status": "FAILED",
            "reason": e.reason_code,
            "detail": e.detail,
        }

    reg = registry or SourceRegistry()
    try:
        reg.register(pin)
    except VersionPinError as e:
        return {
            "ok": False,
            "status": "FAILED",
            "reason": e.reason_code,
            "detail": e.detail,
            "pin_id": pin["pin_id"],
        }

    fetch_plan = build_fetch_plan(pin)
    fetch_result = None
    if execute:
        f = fetcher or FakeFetcher()
        fetch_result = f.execute(fetch_plan)
    else:
        fetch_result = {**fetch_plan, "status": "SKIPPED"}

    install_plan = build_install_plan(
        pin,
        fetch_result=fetch_result if execute else {"status": "SUCCESS"},
        target_dir=target_dir,
    )

    ok = (
        (not execute or (fetch_result or {}).get("status") == "SUCCESS")
        and install_plan.get("status") == "PLANNED"
    )
    status = "COMPLETED" if ok else install_plan.get("status") or "FAILED"
    if execute and (fetch_result or {}).get("status") == "FAILED":
        status = "FAILED"

    return {
        "ok": ok,
        "status": status,
        "pin_id": pin["pin_id"],
        "pin_hash": pin["pin_hash"],
        "fetch_plan": fetch_plan,
        "fetch_result": fetch_result,
        "install_plan": install_plan,
        "license_verdict": (install_plan.get("license") or {}).get("verdict"),
    }
