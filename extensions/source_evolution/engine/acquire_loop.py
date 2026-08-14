# -*- coding: utf-8 -*-
"""acquire_12 loop runner — E9. 0% LLM."""
from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

from .fetch_planner import FakeFetcher, FetcherPort, build_fetch_plan
from .install_planner import build_install_plan
from .license_gate import check_license
from .provenance import build_provenance
from .registry import SourceRegistry
from .version_pin import VersionPinError, normalize_pin


def _loop_path() -> Path:
    return Path(__file__).resolve().parents[1] / "loops" / "acquire_12.yaml"


def load_acquire_12(path: Path | str | None = None) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML required")
    p = Path(path) if path else _loop_path()
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return {
        "loop_id": data.get("loop_id", "acquire_12"),
        "steps": list(data.get("steps") or []),
        "on_fail": data.get("on_fail", "stop"),
        "on_license_stop": data.get("on_license_stop", "stop"),
    }


def run_acquire_12(
    raw_pin: dict[str, Any] | None,
    *,
    loop_path: Path | str | None = None,
    fetcher: FetcherPort | None = None,
    registry: SourceRegistry | None = None,
    execute: bool = True,
    target_dir: str = "vendor",
) -> dict[str, Any]:
    cfg = load_acquire_12(loop_path)
    state: dict[str, Any] = {
        "loop_id": cfg["loop_id"],
        "step_results": [],
        "status": "RUNNING",
        "pin": None,
        "resolve": None,
        "fetch_plan": None,
        "fetch_result": None,
        "license": None,
        "install_plan": None,
        "provenance": None,
        "stop_reason": None,
    }

    def _rec(sid: str, name: str, ok: bool, detail: Any = None) -> None:
        state["step_results"].append(
            {"id": sid, "name": name, "ok": ok, "detail": detail}
        )

    try:
        pin = normalize_pin(raw_pin)
        state["pin"] = pin
        _rec("A01", "normalize_pin", True, pin["pin_id"])
    except VersionPinError as e:
        _rec("A01", "normalize_pin", False, e.reason_code)
        state["status"] = "FAILED"
        state["stop_reason"] = e.reason_code
        return state

    reg = registry or SourceRegistry()
    try:
        reg.register(pin)
        _rec("A02", "registry_register", True, pin["pin_id"])
    except VersionPinError as e:
        _rec("A02", "registry_register", False, e.reason_code)
        state["status"] = "FAILED"
        state["stop_reason"] = e.reason_code
        return state

    resolved = reg.resolve(pin_id=pin["pin_id"])
    state["resolve"] = resolved
    _rec("A03", "registry_resolve", resolved.get("ok", False), resolved.get("reason"))
    if not resolved.get("ok"):
        state["status"] = "FAILED"
        state["stop_reason"] = resolved.get("reason")
        return state

    fetch_plan = build_fetch_plan(pin)
    state["fetch_plan"] = fetch_plan
    _rec("A04", "build_fetch_plan", True, fetch_plan.get("method"))

    fetch_result: dict[str, Any]
    if execute:
        f = fetcher or FakeFetcher()
        fetch_result = f.execute(fetch_plan)
    else:
        fetch_result = {**fetch_plan, "status": "SKIPPED"}
    state["fetch_result"] = fetch_result
    ok_fetch = fetch_result.get("status") in ("SUCCESS", "SKIPPED")
    _rec("A05", "execute_fetch", ok_fetch, fetch_result.get("status"))
    if execute and not ok_fetch:
        state["status"] = "FAILED"
        state["stop_reason"] = "FETCH_FAILED"
        return state

    lic = check_license(pin.get("license"))
    state["license"] = lic
    _rec("A06", "license_gate", lic.get("verdict") != "STOP", lic.get("verdict"))
    if lic.get("verdict") == "STOP" and cfg.get("on_license_stop") == "stop":
        state["status"] = "FAILED"
        state["stop_reason"] = "LICENSE_STOP"
        return state

    install_plan = build_install_plan(
        pin,
        fetch_result=fetch_result if execute else {"status": "SUCCESS"},
        target_dir=target_dir,
    )
    state["install_plan"] = install_plan
    _rec("A07", "build_install_plan", install_plan.get("status") == "PLANNED",
         install_plan.get("status"))

    try:
        prov = build_provenance(pin, fetch_result=fetch_result, install_plan=install_plan)
        state["provenance"] = prov
        _rec("A08", "provenance_record", True, None)
    except Exception as e:  # pragma: no cover
        _rec("A08", "provenance_record", False, str(e)[:80])

    _rec("A09", "tree_probe", True, "SKIPPED_OPTIONAL")
    _rec("A10", "checkpoint", True, pin["pin_hash"])
    _rec("A11", "evidence_stub", True, pin["pin_id"])
    _rec("A12", "next_or_stop", True, "DONE")

    state["status"] = "COMPLETED"
    return state
