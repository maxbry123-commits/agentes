"""YAIWES Agenta STEP3 adapter: validate the real platform build-kit through FABLES."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PLUGIN_ID = "yaiwes.agent_fleet.agenta"
ROLE = "agent_workspace_background_runtime"
TARGET_RELATIVE = "Agente Yaiwes principal/agent-fleet-parallelism/agenta"

REQUIRED_PLATFORM_OPS = {
    "commit_revision",
    "query_spans",
    "test_run",
    "discover_triggers",
    "create_schedule",
    "create_subscription",
    "list_schedules",
    "list_deliveries",
    "test_subscription",
    "remove_schedule",
    "remove_subscription",
}

def descriptor() -> dict[str, str]:
    return {
        "plugin_id": PLUGIN_ID,
        "role": ROLE,
        "microtest": "real_build_kit_background_agent_ops",
    }

def run_microtest(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    target = root / TARGET_RELATIVE
    api = target / "api"
    sdk = target / "sdks" / "python"
    client = target / "clients" / "python"
    for path in (client, sdk, api):
        if not path.is_dir():
            raise RuntimeError(f"AGENTA_RUNTIME_PATH_MISSING:{path}")
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))

    from oss.src.core.workflows.build_kit import build_agent_template_overlay

    overlay = build_agent_template_overlay()
    tools = overlay.get("tools") or []
    platform_tools = [t for t in tools if isinstance(t, dict) and t.get("type") == "platform"]
    op_names = [t.get("op") for t in platform_tools]
    missing = sorted(REQUIRED_PLATFORM_OPS.difference(op_names))
    if missing:
        raise RuntimeError(f"AGENTA_BUILD_KIT_OPS_MISSING:{missing}")
    allowed = [t.get("op") for t in platform_tools if t.get("permission") == "allow"]
    if allowed != ["rename_session", "rename_agent"]:
        raise RuntimeError(f"AGENTA_AUTO_PERMISSION_DRIFT:{allowed}")
    sandbox = overlay.get("sandbox") or {}
    permissions = sandbox.get("permissions") or {}
    if permissions.get("write_files") != "allow" or permissions.get("execute_code") != "allow":
        raise RuntimeError(f"AGENTA_SANDBOX_PERMISSION_DRIFT:{permissions}")
    skills = overlay.get("skills") or []
    if not skills:
        raise RuntimeError("AGENTA_BUILD_KIT_SKILL_MISSING")
    return {
        "status": "PASS",
        "capability": "agent_build_kit_background_runtime",
        "required_ops_verified": sorted(REQUIRED_PLATFORM_OPS),
        "platform_op_count": len(platform_tools),
        "auto_allowed_ops": allowed,
        "sandbox_permissions": permissions,
        "skill_count": len(skills),
    }

def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: agenta_adapter.py <repo_root>")
    result = run_microtest(sys.argv[1])
    print("YAIWES_AGENTA_RESULT=" + json.dumps(result,separators=(",",":")), flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
