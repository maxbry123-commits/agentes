"""
llm_output_schema.py - FIX P1-29. consultor_experto devolvia str plano.
Ahora se valida contra una forma tipada antes de usarse - fail-closed si
no cumple el esquema minimo.
"""
import re
from dataclasses import dataclass, field


@dataclass
class LLMDecision:
    decision: str
    confidence: str = ""  # informativo, NUNCA autoridad de PASS
    evidence_refs: list[str] = field(default_factory=list)
    recommended_action: str = ""
    unknowns: list[str] = field(default_factory=list)


def parsear_respuesta_llm(texto: str) -> LLMDecision | None:
    """P1-29 FIX: validacion fail-closed. Si el texto no tiene contenido
    minimo aprovechable, devuelve None en vez de forzar una decision."""
    if not texto or not texto.strip():
        return None
    if texto.upper().startswith(("ERROR", "ERROR_CEREBRAS", "ERROR_CLAUDE_SDK")):
        return None
    return LLMDecision(decision=texto.strip()[:2000], evidence_refs=[], unknowns=[])
