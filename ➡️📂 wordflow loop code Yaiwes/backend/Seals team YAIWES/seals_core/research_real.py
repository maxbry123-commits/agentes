"""
research_real.py - P1-18 FIX. Antes: 20 intentos volvian a preguntar al
mismo Cerebras, y "RESUELTO" escrito por el modelo se confundia con
resolucion real. Ahora: ResearchResult estructurado, con cross_check
entre fuentes reales, nunca solo la opinion de un LLM repetida.
"""
from dataclasses import dataclass, field


@dataclass
class ResearchResult:
    query: str
    sources: list[str] = field(default_factory=list)
    source_type: str = ""  # ej: "github", "huggingface", "community", "llm_synthesis"
    claims: list[str] = field(default_factory=list)
    cross_check: list[str] = field(default_factory=list)
    new_evidence: bool = False
    conclusion: str = ""

    def es_evidencia_real(self) -> tuple[bool, str]:
        """P1-18 aceptacion: NO_NEW_EVIDENCE -> NO_RESEARCH. 'RESUELTO'
        escrito por un modelo != ejecucion demostrada."""
        if not self.sources:
            return False, "SIN_FUENTES_NO_ES_EVIDENCIA_REAL"
        if self.source_type == "llm_synthesis" and not self.cross_check:
            return False, "SOLO_OPINION_LLM_SIN_CROSS_CHECK_NO_ES_EVIDENCIA"
        if not self.new_evidence:
            return False, "NO_NEW_EVIDENCE_NO_RESEARCH"
        return True, "evidencia_real_con_fuentes_y_cross_check"


def construir_desde_respuesta_llm(query: str, respuesta_llm: str) -> ResearchResult:
    """Envuelve una respuesta de Cerebras/Claude como candidato a
    evidencia - PERO marcada explicitamente como llm_synthesis, nunca
    como fuente primaria. Debe pasar por cross_check antes de contar."""
    return ResearchResult(
        query=query,
        sources=["llm_opinion"],
        source_type="llm_synthesis",
        claims=[respuesta_llm],
        cross_check=[],
        new_evidence=False,
    )
