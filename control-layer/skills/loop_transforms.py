"""Skills/transforms deterministas para D5 loops.
SOURCE: regla del delta · stall · escalada 0% LLM
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib


@dataclass(frozen=True)
class LoopVerdict:
    continue_loop: bool
    reason: str
    escalate_level: int = 0


def parse_loop_yaml(path: str | Path) -> dict[str, Any]:
    import yaml
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stall_detector(prev_hash: str | None, curr_hash: str, identical_limit: int = 2, streak: int = 0) -> tuple[bool, int]:
    """True si estancamiento."""
    if prev_hash and prev_hash == curr_hash:
        streak += 1
    else:
        streak = 0
    return streak >= identical_limit, streak


def delta_gate(score: int, minimo: int) -> bool:
    return score >= minimo


def decide_iteration(
    *,
    iteration: int,
    max_iter: int,
    delta_score: int,
    minimo: int,
    prev_hash: str | None,
    curr_output: str,
    stall_streak: int = 0,
) -> LoopVerdict:
    if iteration >= max_iter:
        return LoopVerdict(False, "max_iteraciones", escalate_level=3)
    h = content_hash(curr_output)
    stalled, streak = stall_detector(prev_hash, h, streak=stall_streak)
    if stalled:
        return LoopVerdict(False, "estancamiento_hash", escalate_level=1)
    if not delta_gate(delta_score, minimo):
        # mutar estrategia primero
        return LoopVerdict(True, "delta_bajo_mutar", escalate_level=1)
    return LoopVerdict(True, "ok", escalate_level=0)


def validate_loop_schema(data: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    loop = data.get("loop") or data
    if not loop.get("id"):
        errors.append("missing id")
    if int(loop.get("max_iteraciones") or 0) < 1:
        errors.append("max_iteraciones < 1")
    if (loop.get("presupuesto") or {}).get("adaptativo") is True:
        errors.append("adaptativo must be false")
    return len(errors) == 0, errors
