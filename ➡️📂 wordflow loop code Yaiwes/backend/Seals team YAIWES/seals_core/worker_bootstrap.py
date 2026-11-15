"""
worker_bootstrap.py - FIX P1-20, P1-21. Antes: task_contract.json solo
declaraba CEREBRAS_API_KEY_1..6 (Handoff exige tambien ANTHROPIC_API_KEY
y GITHUB_TOKEN), y ejecutor.py nunca lo cargaba - era config estatica sin uso.
Ahora: ConfigContract unificado (solo secret REFS, nunca el valor), y
WorkerBootstrap que valida todo ANTES de aceptar cualquier mision.
"""
import os
from dataclasses import dataclass, field


@dataclass
class ConfigContract:
    """Solo nombres de variables de entorno (secret refs), nunca valores."""
    secret_refs: list[str] = field(default_factory=lambda: [
        "CEREBRAS_API_KEY_1", "CEREBRAS_API_KEY_2", "CEREBRAS_API_KEY_3",
        "CEREBRAS_API_KEY_4", "CEREBRAS_API_KEY_5", "CEREBRAS_API_KEY_6",
        "ANTHROPIC_API_KEY", "GITHUB_TOKEN",
    ])
    worker_id: str = ""
    assigned_node: int | None = None
    capability: str = ""
    write_scope: str = ""
    base_sha: str = ""


@dataclass
class BootstrapResult:
    ready: bool
    estado: str
    faltantes: list[str] = field(default_factory=list)


def cargar_y_validar(contract: ConfigContract) -> BootstrapResult:
    """P1-20 aceptacion: startup validation fail-closed ANTES de iniciar
    mision. P1-21 aceptacion: worker no puede ejecutar nodo distinto al
    asignado en el contract."""
    faltantes = [ref for ref in contract.secret_refs if not os.environ.get(ref)]
    if faltantes:
        return BootstrapResult(ready=False, estado="BLOCKED_MISSING_SECRETS", faltantes=faltantes)

    if not contract.worker_id or contract.assigned_node is None:
        return BootstrapResult(ready=False, estado="BLOCKED_CONTRACT_INCOMPLETO", faltantes=["worker_id_o_assigned_node"])

    if not contract.write_scope:
        return BootstrapResult(ready=False, estado="BLOCKED_SIN_WRITE_SCOPE", faltantes=["write_scope"])

    return BootstrapResult(ready=True, estado="READY")


def verificar_nodo_autorizado(contract: ConfigContract, node_id: int) -> tuple[bool, str]:
    """P1-21: worker NO puede ejecutar un nodo distinto al asignado."""
    if contract.assigned_node != node_id:
        return False, f"NODO_NO_AUTORIZADO:asignado={contract.assigned_node}:solicitado={node_id}"
    return True, "nodo_autorizado"
