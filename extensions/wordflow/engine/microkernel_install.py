# -*- coding: utf-8 -*-
"""MicrokernelInstallPlanner — T44. Plan agent installs. 0% LLM.

No git clone / no network. Plans only until HF compute + post-Wordflow.
"""
from __future__ import annotations

from typing import Any

# Known agent slots (adapters later)
AGENT_CATALOG: dict[str, dict[str, Any]] = {
    "openclaw": {
        "role": "planning_engine",
        "port": "PlanningPort",
        "fetchable": False,
        "reason": "post-wordflow + HF compute",
    },
    "hermes": {
        "role": "memory_engine",
        "port": "MemoryPort",
        "fetchable": False,
        "reason": "post-wordflow + HF compute",
    },
    "aider": {"role": "code_engine", "port": "EngineABI", "fetchable": False},
    "cline": {"role": "code_engine", "port": "EngineABI", "fetchable": False},
    "codex": {"role": "code_engine", "port": "EngineABI", "fetchable": False},
    "mimo": {"role": "code_engine", "port": "EngineABI", "fetchable": False},
}


class MicrokernelInstallPlanner:
    def __init__(self, catalog: dict[str, dict[str, Any]] | None = None):
        self.catalog = dict(catalog or AGENT_CATALOG)

    def list_agents(self) -> list[dict[str, Any]]:
        return [
            {"agent_id": k, **dict(v)} for k, v in self.catalog.items()
        ]

    def plan_install(self, agent_id: str) -> dict[str, Any]:
        meta = self.catalog.get(agent_id)
        if not meta:
            return {"ok": False, "reason": "UNKNOWN_AGENT", "agent_id": agent_id}
        if not meta.get("fetchable"):
            return {
                "ok": False,
                "action": "DEFERRED",
                "agent_id": agent_id,
                "role": meta.get("role"),
                "port": meta.get("port"),
                "reason": meta.get("reason") or "fetchable=false",
                "next": ["finish_wordflow", "attach_hf_compute", "enable_fetch"],
            }
        return {
            "ok": True,
            "action": "INSTALL_PLANNED",
            "agent_id": agent_id,
            "steps": [
                "resolve_source",
                "verify_checksum",
                "place_under_extensions/engines",
                "register_ExtensionRegistry",
                "wire_port",
            ],
        }

    def plan_batch(self, agent_ids: list[str]) -> dict[str, Any]:
        plans = [self.plan_install(a) for a in agent_ids]
        deferred = sum(1 for p in plans if p.get("action") == "DEFERRED")
        return {
            "ok": True,
            "n": len(plans),
            "deferred": deferred,
            "plans": plans,
        }
