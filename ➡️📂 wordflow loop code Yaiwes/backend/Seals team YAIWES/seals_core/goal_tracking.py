"""
goal_tracking.py - P0-05 FIX (integracion Meta Muse Code: goal tracking +
completion audit). No se cierra un nodo por texto del agente ni por
numero de iteraciones - solo cuando CADA acceptance[] esta demostrada.
"""
from dataclasses import dataclass, field


@dataclass
class GoalContract:
    goal_id: str
    objective: str
    acceptance: list[str] = field(default_factory=list)
    evidence_por_acceptance: dict = field(default_factory=dict)
    state: str = "DECLARED"
    completion_status: str = "OPEN"

    def declarar(self) -> None:
        self.state = "DECLARED"
        self.completion_status = "OPEN"

    def registrar_evidencia_de_acceptance(self, acceptance_id: str, evidence_record) -> None:
        """Asocia un EvidenceRecord (de evidence.py) a un criterio concreto."""
        self.evidence_por_acceptance[acceptance_id] = evidence_record
        self.state = "WORKING"

    def completion_audit(self) -> tuple[bool, str]:
        """P0-05 aceptacion: no existe transicion CLOSED si acceptance[]
        no esta COMPLETAMENTE demostrada. Nunca se cierra por texto del
        agente ni por conteo de iteraciones."""
        if not self.acceptance:
            return False, "SIN_ACCEPTANCE_DECLARADO_NO_SE_PUEDE_CERRAR"
        faltantes = [a for a in self.acceptance if a not in self.evidence_por_acceptance]
        if faltantes:
            self.completion_status = "OPEN"
            return False, f"ACCEPTANCE_SIN_DEMOSTRAR:{','.join(faltantes)}"
        for acceptance_id, ev in self.evidence_por_acceptance.items():
            ok, motivo = ev.es_valida()
            if not ok:
                self.completion_status = "OPEN"
                return False, f"EVIDENCIA_INVALIDA_EN:{acceptance_id}:{motivo}"
        self.state = "CLOSED"
        self.completion_status = "VERIFIED_CLOSED"
        return True, "todas_las_acceptance_demostradas_con_evidencia_valida"
