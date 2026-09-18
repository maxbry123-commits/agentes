"""
recovery_types.py - FIX P1-26. Antes: catch Exception -> GAP generico
para todo. Ahora: cada fallo se clasifica en una categoria tipada, con
politica concreta de retry/recovery/block por categoria.
"""
from enum import Enum


class ClaseDeFallo(str, Enum):
    RETRYABLE = "RETRYABLE"
    DEPENDENCY = "DEPENDENCY"
    AUTH = "AUTH"
    STUCK = "STUCK"
    CRASH = "CRASH"
    IRREVERSIBLE_FAILURE = "IRREVERSIBLE_FAILURE"
    NO_NODE_SOLUTION = "NO_NODE_SOLUTION"


POLITICA_POR_CLASE = {
    ClaseDeFallo.RETRYABLE: "reintentar_con_backoff",
    ClaseDeFallo.DEPENDENCY: "bloquear_hasta_que_dependencia_resuelva",
    ClaseDeFallo.AUTH: "bloquear_y_avisar_credenciales",
    ClaseDeFallo.STUCK: "cambiar_estrategia_o_bloquear_con_traza",
    ClaseDeFallo.CRASH: "resumir_desde_checkpoint",
    ClaseDeFallo.IRREVERSIBLE_FAILURE: "compensar_y_registrar",
    ClaseDeFallo.NO_NODE_SOLUTION: "pasar_a_siguiente_nodo_independiente",
}


def clasificar_fallo(error_type: str, mensaje: str = "") -> ClaseDeFallo:
    """P1-26 FIX: clasificacion real en vez de GAP generico. Heuristica
    basada en el error_type (de ToolResult, P0-17) y el mensaje."""
    et = (error_type or "").upper()
    msg = (mensaje or "").upper()

    if "AUTH" in et or "NO_CEREBRAS_API_KEY" in msg or "GITHUB_TOKEN" in msg:
        return ClaseDeFallo.AUTH
    if "TIMEOUT" in et or "NETWORK" in et or et == "GIT_CLONE_FAILED":
        return ClaseDeFallo.RETRYABLE
    if "DEPENDENCY" in et or "REPO_DISTINTO" in msg:
        return ClaseDeFallo.DEPENDENCY
    if "STUCK" in et or "BLOCKED_STUCK" in msg:
        return ClaseDeFallo.STUCK
    if "CRASH" in et or "PROCESS_DIED" in msg:
        return ClaseDeFallo.CRASH
    if "INTEGRITY_MISMATCH" in et or "COMMIT_DIVERGIO" in msg:
        return ClaseDeFallo.IRREVERSIBLE_FAILURE
    return ClaseDeFallo.NO_NODE_SOLUTION


def politica_para(clase: ClaseDeFallo) -> str:
    return POLITICA_POR_CLASE.get(clase, "pasar_a_siguiente_nodo_independiente")
