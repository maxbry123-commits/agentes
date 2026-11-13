"""
sheriff_policy.py - P0-15 FIX. Ninguna accion con side effect (git clone,
pip install, escritura de archivo) se ejecuta sin pasar por aqui primero.
Regla dura: el LLM propone, esto autoriza (o no), nunca al reves.
"""
from dataclasses import dataclass
from pathlib import Path

ACCIONES_PERMITIDAS = {"git_clone", "pip_install", "file_write", "verificar_existencia"}


@dataclass
class StructuredAction:
    action: str
    target_path: str
    params: dict


def aprobar(accion: StructuredAction, workspace_raiz: Path) -> tuple[bool, str]:
    """P0-15 aceptacion: LLM nunca ejecuta directamente - toda accion pasa
    por este gate. Fail-closed: si algo no esta explicitamente permitido,
    se deniega."""
    if accion.action not in ACCIONES_PERMITIDAS:
        return False, f"ACCION_NO_PERMITIDA:{accion.action}"

    destino = Path(accion.target_path)
    try:
        destino_resuelto = (workspace_raiz / destino).resolve()
        workspace_resuelto = workspace_raiz.resolve()
    except Exception:
        return False, "PATH_INVALIDO"

    # Evita path traversal: el destino debe quedar DENTRO del workspace.
    if workspace_resuelto not in destino_resuelto.parents and destino_resuelto != workspace_resuelto:
        return False, "PATH_TRAVERSAL_DETECTADO_FUERA_DE_WORKSPACE"

    return True, "APROBADO"
