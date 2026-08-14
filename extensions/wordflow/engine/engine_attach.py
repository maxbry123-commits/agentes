# -*- coding: utf-8 -*-
"""engine_attach — D2/T3. Wire PlanningPort/MemoryPort. 0% LLM structure.

Real OpenClaw/Hermes: DEFERRED (PIPELINE/32 + D3 HF compute).
This module only registers ports; never imports real agent code.
"""
from __future__ import annotations

from typing import Any

from .ports.memory_port import FakeHermesMemory, MemoryPort
from .ports.planning_port import FakeHermesPlanner, FakeOpenClawPlanner, PlanningPort


class EngineAttachRegistry:
    """Holds active planning/memory ports. Swap without redesign."""

    def __init__(self):
        self.planning: PlanningPort = FakeOpenClawPlanner()
        self.memory: MemoryPort = FakeHermesMemory()
        self.allow_real = False
        self._meta: dict[str, Any] = {
            "planning": "FakeOpenClawPlanner",
            "memory": "FakeHermesMemory",
        }

    def attach_planning(
        self,
        port: PlanningPort,
        *,
        name: str = "custom",
        is_real: bool = False,
    ) -> dict[str, Any]:
        if is_real and not self.allow_real:
            return {
                "ok": False,
                "reason": "REAL_ENGINE_DISABLED",
                "next": ["finish_wordflow", "HF_compute", "D3_fetch", "set allow_real"],
            }
        self.planning = port
        self._meta["planning"] = name
        return {"ok": True, "planning": name}

    def attach_memory(
        self,
        port: MemoryPort,
        *,
        name: str = "custom",
        is_real: bool = False,
    ) -> dict[str, Any]:
        if is_real and not self.allow_real:
            return {
                "ok": False,
                "reason": "REAL_ENGINE_DISABLED",
                "next": ["finish_wordflow", "HF_compute", "D3_fetch", "set allow_real"],
            }
        self.memory = port
        self._meta["memory"] = name
        return {"ok": True, "memory": name}

    def enable_real(self, flag: bool = True) -> dict[str, Any]:
        """Director-only switch when infra ready."""
        self.allow_real = bool(flag)
        return {"ok": True, "allow_real": self.allow_real}

    def plan(self, contract: dict[str, Any], form: dict[str, Any]) -> dict[str, Any]:
        """Delegate to PlanningPort.propose(contract, form)."""
        return self.planning.propose(contract, form)

    def refresh_memory(
        self,
        lock: dict[str, Any],
        *,
        current_step: str | None = None,
        last_output: str | None = None,
        checkpoint_ref: str | None = None,
    ) -> dict[str, Any]:
        """Delegate to MemoryPort.refresh."""
        return self.memory.refresh(
            lock,
            current_step=current_step,
            last_output=last_output,
            checkpoint_ref=checkpoint_ref,
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "allow_real": self.allow_real,
            "ports": dict(self._meta),
            "planning_type": type(self.planning).__name__,
            "memory_type": type(self.memory).__name__,
        }


def default_attach() -> EngineAttachRegistry:
    reg = EngineAttachRegistry()
    reg.attach_planning(FakeOpenClawPlanner(), name="FakeOpenClawPlanner")
    reg.attach_memory(FakeHermesMemory(), name="FakeHermesMemory")
    return reg
