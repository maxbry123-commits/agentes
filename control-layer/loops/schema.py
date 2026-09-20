from dataclasses import dataclass
from typing import Literal

LoopId = Literal[
    "L01", "L02", "L03", "L04", "L05", "L06",
    "L07", "L08", "L09", "L10", "L11",
]


@dataclass(frozen=True)
class LoopDefinition:
    """Schema de un Loop (SOURCE: SALIDA_1_CAPA_CONTROL_PARTE_3 §36)."""
    id: LoopId
    proposito: str
    max_iteraciones: int = 3
    delta_minimo: int = 10  # score 0-100


LOOPS: dict[LoopId, LoopDefinition] = {
    "L01": LoopDefinition("L01", "Planificación", 3),
    "L02": LoopDefinition("L02", "Ejecución", 5),
    "L03": LoopDefinition("L03", "Validación", 3),
    "L04": LoopDefinition("L04", "Reparación", 3),
    "L05": LoopDefinition("L05", "Aprendizaje", 2),
    "L06": LoopDefinition("L06", "Optimización", 2),
    "L07": LoopDefinition("L07", "Auditoría", 2),
    "L08": LoopDefinition("L08", "Consenso", 3),
    "L09": LoopDefinition("L09", "Memoria", 2),
    "L10": LoopDefinition("L10", "Recuperación", 3),
    "L11": LoopDefinition("L11", "Cierre", 1),
}

# Interconexión clave: L03 falla → L04 repara → vuelve a L03 (máx 3 ciclos)
