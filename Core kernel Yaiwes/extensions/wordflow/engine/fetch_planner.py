# -*- coding: utf-8 -*-
"""FetchPlanner — D3. Deterministic fetch plan for HF/git. 0% LLM.

Default: no network. allow_fetch=True only after Director + HF compute.
"""
from __future__ import annotations

import hashlib
from typing import Any

from .hf_index import HFResourceIndex
from .microkernel_install import MicrokernelInstallPlanner


def _sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


class FetchPlanner:
    def __init__(
        self,
        *,
        hf_index: HFResourceIndex | None = None,
        agents: MicrokernelInstallPlanner | None = None,
        allow_fetch: bool = False,
    ):
        self.hf_index = hf_index or HFResourceIndex()
        self.agents = agents or MicrokernelInstallPlanner()
        self.allow_fetch = bool(allow_fetch)

    def enable_fetch(self, flag: bool = True) -> dict[str, Any]:
        self.allow_fetch = bool(flag)
        return {"ok": True, "allow_fetch": self.allow_fetch}

    def plan_hf(self, resource_id: str) -> dict[str, Any]:
        base = self.hf_index.request_fetch(resource_id)
        if not base.get("ok"):
            return base
        if not self.allow_fetch:
            return {
                "ok": False,
                "action": "FETCH_BLOCKED",
                "reason": "allow_fetch=false",
                "planned": base,
                "next": ["Director enable_fetch", "HF_compute online"],
            }
        return {
            "ok": True,
            "action": "FETCH_READY",
            "resource_id": resource_id,
            "hf_id": base.get("hf_id"),
            "revision": base.get("revision"),
            "steps": [
                "resolve_hf_url",
                "download_to_cache",
                "verify_checksum",
                "register_ExtensionRegistry",
            ],
            "execute": False,  # executor not attached in D3
        }

    def plan_agent(self, agent_id: str) -> dict[str, Any]:
        p = self.agents.plan_install(agent_id)
        if p.get("action") == "DEFERRED" and not self.allow_fetch:
            return p
        if not self.allow_fetch:
            return {
                "ok": False,
                "action": "FETCH_BLOCKED",
                "agent_id": agent_id,
                "reason": "allow_fetch=false",
            }
        # mark catalog fetchable only in plan output — does not mutate global policy
        return {
            "ok": True,
            "action": "AGENT_FETCH_READY",
            "agent_id": agent_id,
            "steps": p.get("steps")
            or [
                "resolve_source",
                "verify_checksum",
                "place_under_extensions/engines",
                "register_ExtensionRegistry",
                "wire_port",
            ],
            "execute": False,
        }

    def verify_checksum(self, content: str, expected_sha256: str) -> dict[str, Any]:
        got = _sha256_text(content)
        ok = got == expected_sha256
        return {"ok": ok, "got": got, "expected": expected_sha256}
