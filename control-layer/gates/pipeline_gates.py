"""Orquestación de gates IA 0% críticos antes de ejecutar.
SOURCE: SALIDA_6 · G30 · G28 · G31 · L11
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from .g30_determinismo import g30_determinismo, G30Result
from .g28_suficiencia import g28_suficiencia, Confidence
from .g31_repeticion import g31_repeticion, G31Result


@dataclass(frozen=True)
class GatesVerdict:
    proceed: bool
    requires_llm: bool
    reason: str
    g30: G30Result
    g28: Confidence
    g31: G31Result


def run_critical_gates(
    *,
    task_key: str,
    cache: dict[str, dict[str, Any]],
    has_script: bool = False,
    has_playbook: bool = False,
    fixed_transform: bool = False,
    needs_judgment: bool = False,
    research: int = 0,
    tests: int = 0,
    docs: int = 0,
    experience: int = 0,
) -> GatesVerdict:
    g31 = g31_repeticion(task_key, cache)
    if g31.hit:
        return GatesVerdict(True, False, "cache hit G31", g30_determinismo(already_solved=True), g28_suficiencia(100, 100, 100, 100), g31)

    g30 = g30_determinismo(
        has_script=has_script,
        has_playbook=has_playbook,
        fixed_transform=fixed_transform,
        needs_judgment=needs_judgment,
    )
    g28 = g28_suficiencia(research, tests, docs, experience)

    if not g28.ok:
        return GatesVerdict(False, False, f"suficiencia {g28.score}<70", g30, g28, g31)

    if g30.requires_llm:
        return GatesVerdict(True, True, g30.reason, g30, g28, g31)

    return GatesVerdict(True, False, g30.reason, g30, g28, g31)
