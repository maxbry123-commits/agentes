"""Event hash chain verify · 0% LLM
SOURCE: P1 · loop_event.schema
"""
from __future__ import annotations
import hashlib
from typing import Any, Iterable

from loops.contracts.types import LoopEvent


def compute_hash(event_id: str, run_id: str, etype: str, payload: Any, prev_hash: str) -> str:
    raw = f"{event_id}|{run_id}|{etype}|{payload}|{prev_hash}"
    return hashlib.sha256(raw.encode()).hexdigest()


def verify_chain(events: Iterable[LoopEvent]) -> tuple[bool, str]:
    """Verifica cadena append-only. Retorna (ok, reason)."""
    prev = ""
    for i, ev in enumerate(events):
        if ev.prev_hash != prev:
            return False, f"break at index {i}: prev_hash mismatch"
        expected = compute_hash(ev.event_id, ev.run_id, ev.type, ev.payload, ev.prev_hash)
        if ev.hash != expected:
            return False, f"break at index {i}: hash mismatch"
        prev = ev.hash
    return True, "ok"
