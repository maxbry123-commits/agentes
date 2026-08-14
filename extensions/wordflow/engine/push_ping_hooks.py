# -*- coding: utf-8 -*-
"""Push/Ping memory refresh hooks — T0q. Optional MemoryPort. 0% LLM."""
from __future__ import annotations

from typing import Any, Protocol

from .push_ping import DEFAULT_FOCUS_THRESHOLD, DEFAULT_INTERVAL_S, PushPingSupervisor, emit_ping


class _MemoryPortLike(Protocol):
    def refresh(
        self,
        lock: dict[str, Any],
        *,
        current_step: str | None = None,
        last_output: str | None = None,
        checkpoint_ref: str | None = None,
    ) -> dict[str, Any]: ...


class PushPingWithMemory(PushPingSupervisor):
    """Supervisor + optional MemoryPort on degraded focus / every N interval pings."""

    def __init__(
        self,
        lock: dict[str, Any],
        *,
        interval_s: float = DEFAULT_INTERVAL_S,
        focus_threshold: float = DEFAULT_FOCUS_THRESHOLD,
        memory_port: _MemoryPortLike | None = None,
        memory_on_focus_degraded: bool = True,
        memory_every_n_interval: int = 4,
        memory_enabled: bool = True,
        on_event=None,
    ):
        super().__init__(
            lock,
            interval_s=interval_s,
            focus_threshold=focus_threshold,
            on_event=on_event,
        )
        self.memory_port = memory_port
        self.memory_on_focus_degraded = memory_on_focus_degraded
        self.memory_every_n_interval = max(1, memory_every_n_interval)
        self.memory_enabled = memory_enabled
        self._interval_ping_count = 0
        self.last_memory_pack: dict[str, Any] | None = None

    def _maybe_refresh_memory(
        self,
        event: dict[str, Any],
        *,
        current_step: str | None,
        last_output: str | None,
        checkpoint_ref: str | None,
        force: bool = False,
    ) -> dict[str, Any] | None:
        if not self.memory_enabled or self.memory_port is None:
            return None
        degraded = event.get("action") == "STOP_REPLAN" and "focus_below" in " ".join(
            event.get("reasons") or []
        )
        every_n = False
        if event.get("trigger") == "interval":
            self._interval_ping_count += 1
            every_n = self._interval_ping_count % self.memory_every_n_interval == 0

        if not force and not (
            (self.memory_on_focus_degraded and degraded) or every_n
        ):
            return None

        pack = self.memory_port.refresh(
            self.lock,
            current_step=current_step,
            last_output=last_output,
            checkpoint_ref=checkpoint_ref,
        )
        self.last_memory_pack = pack
        return pack

    def maybe_interval_ping(
        self,
        *,
        current_step: str | None = None,
        last_output: str | None = None,
        lease_alive: bool = True,
        checkpoint_ref: str | None = None,
        now_mono: float | None = None,
    ) -> dict[str, Any] | None:
        ev = super().maybe_interval_ping(
            current_step=current_step,
            last_output=last_output,
            lease_alive=lease_alive,
            checkpoint_ref=checkpoint_ref,
            now_mono=now_mono,
        )
        if ev is None:
            return None
        pack = self._maybe_refresh_memory(
            ev,
            current_step=current_step,
            last_output=last_output,
            checkpoint_ref=checkpoint_ref,
        )
        if pack is not None:
            ev = dict(ev)
            ev["memory_pack_id"] = pack.get("pack_id")
            # re-hash not required for supervisor side channel
        return ev

    def post_tool_ping(
        self,
        *,
        current_step: str | None = None,
        last_output: str | None = None,
        lease_alive: bool = True,
        checkpoint_ref: str | None = None,
    ) -> dict[str, Any]:
        ev = super().post_tool_ping(
            current_step=current_step,
            last_output=last_output,
            lease_alive=lease_alive,
            checkpoint_ref=checkpoint_ref,
        )
        pack = self._maybe_refresh_memory(
            ev,
            current_step=current_step,
            last_output=last_output,
            checkpoint_ref=checkpoint_ref,
        )
        if pack is not None:
            ev = dict(ev)
            ev["memory_pack_id"] = pack.get("pack_id")
        return ev


def load_ping_policy(yaml_dict: dict[str, Any] | None = None) -> dict[str, Any]:
    """Normalize policy dict (from engine_attach.yaml ping section)."""
    ping = (yaml_dict or {}).get("ping") if yaml_dict else None
    ping = ping or {}
    mr = ping.get("memory_refresh") or {}
    return {
        "interval_s": float(ping.get("interval_s", DEFAULT_INTERVAL_S)),
        "focus_threshold": float(ping.get("focus_threshold", DEFAULT_FOCUS_THRESHOLD)),
        "memory_enabled": bool(mr.get("enabled", True)),
        "memory_on_focus_degraded": bool(mr.get("on_focus_degraded", True)),
        "memory_every_n_interval": int(mr.get("every_n_interval_pings", 4)),
    }
