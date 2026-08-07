from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class InputGoal:
    """12 campos fijos de entrada (SOURCE: SALIDA_1_CAPA_CONTROL_PARTE_3)."""
    objective: str                    # G-IN-01  1 sola acción
    agente_destino: str               # G-IN-02
    destino_final: str                # G-IN-03  VPS_REAL|GITHUB + ruta
    constraints: tuple[str, ...]      # G-IN-04
    success_criteria: str             # G-IN-05  comando ejecutable
    prioridad: Literal["BLOQUEANTE", "NORMAL", "BACKLOG"]  # G-IN-06
    credencial: str                   # G-IN-07
    depende_de: str                   # G-IN-08  trace_id | NINGUNA
    skill: str                        # G-IN-09
    entorno: str                      # G-IN-10
    rollback: str                     # G-IN-11  comando ejecutable
    aprobador: str                    # G-IN-12  Council|Max


@dataclass(frozen=True)
class OutputGoal:
    """12 campos fijos de salida."""
    trace_id: str
    destino_final_alcanzado: bool
    comando_output_crudo: str
    fuentes_cruzadas: int             # ≥2
    refute_consistente: bool
    estado_final: Literal["SUCCESS", "FAIL", "WAITING_APPROVAL", "ROLLBACK"]
    prohibidos_intactos: bool
    cadena_de_saltos: str
    checkpoint_actualizado: bool
    root_cause: str | None
    next_action: str                  # NONE
    registrado_github: bool
