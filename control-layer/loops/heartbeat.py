"""Heartbeat — liveness de runs · 0% LLM
SOURCE: Fase 4 · distingue RUNNING vs STALLED vs DEAD
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

Health = Literal["ACTIVE", "STALLED", "DEAD", "UNKNOWN"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class HeartbeatRecord:
    run_id: str
    last_beat: datetime
    owner: str = ""


class HeartbeatMonitor:
    def __init__(self, stall_seg: int = 60, dead_seg: int = 180) -> None:
        self.stall_seg = stall_seg
        self.dead_seg = dead_seg
        self._beats: dict[str, HeartbeatRecord] = {}

    def beat(self, run_id: str, owner: str = "") -> None:
        self._beats[run_id] = HeartbeatRecord(run_id=run_id, last_beat=_now(), owner=owner)

    def health(self, run_id: str) -> Health:
        rec = self._beats.get(run_id)
        if not rec:
            return "UNKNOWN"
        age = (_now() - rec.last_beat).total_seconds()
        if age > self.dead_seg:
            return "DEAD"
        if age > self.stall_seg:
            return "STALLED"
        return "ACTIVE"

    def stalled_or_dead(self) -> dict[str, Health]:
        out: dict[str, Health] = {}
        for rid in self._beats:
            h = self.health(rid)
            if h in ("STALLED", "DEAD"):
                out[rid] = h
        return out

    def remove(self, run_id: str) -> None:
        self._beats.pop(run_id, None)
