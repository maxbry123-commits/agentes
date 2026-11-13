# -*- coding: utf-8 -*-
"""Install planner — A-SE-03. Post-fetch install plan. 0% LLM."""
from __future__ import annotations

from typing import Any

from .license_gate import check_license
from .version_pin import normalize_pin


def build_install_plan(
    raw_pin: dict[str, Any] | None,
    *,
    fetch_result: dict[str, Any] | None = None,
    target_dir: str = "vendor",
) -> dict[str, Any]:
    pin = normalize_pin(raw_pin)
    lic = check_license(pin.get("license"))

    if lic["blocked"]:
        return {
            "plan_id": f"install-{pin['pin_id']}",
            "pin_id": pin["pin_id"],
            "status": "BLOCKED",
            "license": lic,
            "steps": [],
            "reason": "LICENSE_STOP",
        }
    if lic["needs_director"]:
        return {
            "plan_id": f"install-{pin['pin_id']}",
            "pin_id": pin["pin_id"],
            "status": "NEEDS_DIRECTOR",
            "license": lic,
            "steps": [],
            "reason": "LICENSE_DIRECTOR",
        }

    if fetch_result and fetch_result.get("status") != "SUCCESS":
        return {
            "plan_id": f"install-{pin['pin_id']}",
            "pin_id": pin["pin_id"],
            "status": "BLOCKED",
            "license": lic,
            "steps": [],
            "reason": "FETCH_NOT_SUCCESS",
        }

    artifact = (fetch_result or {}).get("artifact_dir") or f"artifacts/sources/{pin['pin_id']}"
    st = pin["source_type"]
    steps: list[dict[str, Any]] = [
        {"op": "verify_artifact", "path": artifact},
    ]
    if st in ("git", "local"):
        steps.append({
            "op": "copy_tree",
            "src": artifact,
            "dst": f"{target_dir}/{pin['pin_id']}",
        })
    elif st == "package":
        steps.append({
            "op": "pip_install_local",
            "path": artifact,
            "note": "uses LOCAL_ARTIFACT only — never live registry",
        })
    elif st in ("hf", "release", "url"):
        steps.append({
            "op": "place_files",
            "src": artifact,
            "dst": f"{target_dir}/{pin['pin_id']}",
        })
    steps.append({
        "op": "write_provenance",
        "pin_id": pin["pin_id"],
        "pin_hash": pin["pin_hash"],
        "digest": pin["digest"],
    })

    return {
        "plan_id": f"install-{pin['pin_id']}",
        "pin_id": pin["pin_id"],
        "status": "PLANNED",
        "license": lic,
        "steps": steps,
        "target_dir": target_dir,
        "llm_control": "DENY",
    }
