"""
evidence.py - P0-06 FIX. EvidenceRecord tipado. Un PASS sin EvidenceRecord
valido queda rechazado - ya no basta con escribir un JSONL suelto.
"""
import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EvidenceRecord:
    path: str
    mission_id: str
    node_id: str
    operation: str
    sha256: str = ""
    tool_receipt: str = ""
    test_result: str = ""
    exit_code: int | None = None
    artifact: str = ""
    source_commit: str = ""
    acceptance_id: str = ""
    timestamp: float = field(default_factory=time.time)

    def es_valida(self) -> tuple[bool, str]:
        """P0-06: campos minimos obligatorios para que un PASS sea aceptado."""
        if not self.path:
            return False, "falta_path"
        if not self.mission_id or not self.node_id:
            return False, "falta_mission_o_node_id"
        if not self.operation:
            return False, "falta_operation"
        if not self.sha256:
            return False, "falta_sha256"
        return True, "ok"


def calcular_sha256_archivo(ruta: Path) -> str:
    if not ruta.exists() or not ruta.is_file():
        return ""
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(8192), b""):
            h.update(bloque)
    return h.hexdigest()


def exigir_evidencia_para_pass(status: str, evidence: EvidenceRecord | None) -> tuple[str, str]:
    """P0-06 aceptacion: PASS sin EvidenceRecord valido -> rechazado (GAP)."""
    if status != "PASS":
        return status, "no_aplica_no_es_pass"
    if evidence is None:
        return "GAP", "PASS_SIN_EVIDENCE_RECORD_RECHAZADO"
    ok, motivo = evidence.es_valida()
    if not ok:
        return "GAP", f"EVIDENCE_RECORD_INVALIDO:{motivo}"
    return "PASS", "evidence_record_valido"
