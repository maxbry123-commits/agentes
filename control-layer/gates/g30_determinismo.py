"""G30 DETERMINISMO — el gate más importante de la capa.
SOURCE: SALIDA_6 · APORTES_1_CAPA_CONTROL
IA 0%. Si se puede sin LLM, no se llama LLM.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class G30Result:
    requires_llm: bool
    reason: str
    action: str  # execute_script | execute_playbook | return_cached | call_llm


def g30_determinismo(
    *,
    has_script: bool = False,
    has_playbook: bool = False,
    already_solved: bool = False,
    fixed_transform: bool = False,
    needs_judgment: bool = False,
    needs_natural_language: bool = False,
    needs_choice_without_rule: bool = False,
) -> G30Result:
    if has_script:
        return G30Result(False, "existe script determinista", "execute_script")
    if has_playbook:
        return G30Result(False, "existe playbook probado", "execute_playbook")
    if already_solved:
        return G30Result(False, "tarea ya resuelta (G31)", "return_cached")
    if fixed_transform:
        return G30Result(False, "transformación con regla fija", "execute_script")

    if needs_judgment or needs_natural_language or needs_choice_without_rule:
        return G30Result(True, "requiere juicio/NL/elección sin regla", "call_llm")

    return G30Result(False, "ninguna razón para LLM", "execute_script")
